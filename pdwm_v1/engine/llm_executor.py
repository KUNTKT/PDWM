# engine/llm_executor.py
from __future__ import annotations
import os, hashlib
from typing import Optional, Type
from pydantic import BaseModel, ValidationError
from diskcache import Cache
from tenacity import retry, stop_after_attempt, wait_fixed
from openai import OpenAI

_cache = Cache(".cache")
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def _extract_json(text: str) -> str:
    # 仅提取最外层 { ... } JSON
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found.")
    return text[start:end+1]

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
def call_llm_structured(*, prompt: str, schema_model: Type[BaseModel],
                        model: str, temperature: float, max_tokens: int,
                        cache_key: Optional[str]=None):
    key = f"{model}:{_sha(prompt)}:{temperature}:{max_tokens}:{cache_key or ''}"
    cached = _cache.get(key)
    if cached:
        return schema_model.model_validate_json(cached)

    resp = _client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role":"system","content":"你只能输出严格的JSON，不要输出解释或多余文本。"},
            {"role":"user","content": prompt}
        ]
    )
    text = resp.choices[0].message.content or ""
    data = _extract_json(text)
    try:
        obj = schema_model.model_validate_json(data)
    except ValidationError as e:
        # 抛出让 tenacity 重试一次
        raise e
    _cache.set(key, obj.model_dump_json())
    return obj

