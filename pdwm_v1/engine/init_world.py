# engine/init_world.py
from __future__ import annotations
import json, os
from typing import Dict, Any, List
from pydantic import BaseModel
from engine.config import load_config
from engine.llm_executor import call_llm_structured
from engine.store import dump_json, append_jsonl

# 轻量校验容器
class InitTriplet(BaseModel):
    world: Dict[str, Any]
    entities: Dict[str, Any]
    events: List[Dict[str, Any]]

def run_init():
    cfg = load_config()
    with open("prompts/init_world.txt","r",encoding="utf-8") as f:
        template = f.read()
    prompt = template.replace("{{CONFIG}}", json.dumps(cfg.init, ensure_ascii=False))

    obj = call_llm_structured(
        prompt=prompt,
        schema_model=InitTriplet,
        model=cfg.model, temperature=cfg.temperature, max_tokens=cfg.max_tokens,
        cache_key="init_world"
    )

    os.makedirs("data", exist_ok=True)
    dump_json("data/world.json", obj.world)
    dump_json("data/entities.json", obj.entities)
    dump_json("data/events.json", obj.events)
    append_jsonl("data/world_log.jsonl", {"t":0, "event":"init", "player_location": cfg.init.get("start","unknown")})
    print("[OK] 初始化完成：data/world.json, entities.json, events.json 已生成。")
