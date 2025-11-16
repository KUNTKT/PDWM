# engine/dialog.py （开头）

from __future__ import annotations
from typing import List, Dict, Any
import json

from pydantic import BaseModel, Field

from engine.config import load_config
from engine.context import load_world_state, get_recent_logs
from engine.llm_executor import call_llm_structured
from engine.schemas import NpcUpdate
from engine.apply_diff import apply_npc_update
from engine.store import dump_json, append_jsonl

class DialogResponse(BaseModel):
    npc_update: NpcUpdate
    utterance_text: str = Field(min_length=1, max_length=200)


def _collect_npc_context(npc_id: str,
                         logs_window: int = 30,
                         max_dialog_logs: int = 6,
                         max_memory: int = 5):
    """
    收集 NPC 对话上下文：
    - world/entities 三件套
    - NPC 自身信息（role, location, memory）
    - 所在空间的 visible_state
    - 最近若干条与该 NPC 相关的对话日志
    """
    world, entities, events = load_world_state()

    if npc_id not in entities:
        raise ValueError(f"NPC {npc_id} 不存在。")

    npc = entities[npc_id]
    role = npc.get("role", "unknown")
    location = npc.get("location", "unknown")
    memory = npc.get("memory", []) or []
    memory_tail = memory[-max_memory:] if max_memory > 0 else memory

    # 所在空间的可视描述
    space = world.get(location, {})
    visible_state = space.get("visible_state", "")

    # 最近与该 NPC 相关的对话日志
    logs = get_recent_logs(logs_window)
    dialog_logs: List[Dict[str, Any]] = []
    for rec in logs[::-1]:  # 从新到旧扫描
        if rec.get("event") == "dialog" and rec.get("npc_id") == npc_id:
            dialog_logs.append(rec)
        if len(dialog_logs) >= max_dialog_logs:
            break
    dialog_logs = dialog_logs[::-1]  # 再按时间正序

    return {
        "world": world,
        "entities": entities,
        "events": events,
        "npc": npc,
        "role": role,
        "location": location,
        "visible_state": visible_state,
        "memory_tail": memory_tail,
        "dialog_logs": dialog_logs,
    }



def run_dialog(npc_id: str, player_input: str) -> str:
    """
    玩家与某 NPC 对话：
    - 收集 NPC 上下文
    - 调用 LLM 生成 npc_update + 自然语言回复
    - 应用 npc_update 写回 entities.json
    - 记录 dialog 日志
    - 返回回复文本
    """
    cfg = load_config()
    ctx = _collect_npc_context(npc_id)

    # 把上下文序列化为 JSON 字符串喂给 prompt
    npc_memory_json = json.dumps(ctx["memory_tail"], ensure_ascii=False, indent=2)
    dialog_logs_json = json.dumps(ctx["dialog_logs"], ensure_ascii=False, indent=2)

    with open("prompts/dialog.txt", "r", encoding="utf-8") as f:
        template = f.read()

    prompt = (
        template
        .replace("{{NPC_ID}}", npc_id)
        .replace("{{ROLE}}", ctx["role"])
        .replace("{{LOCATION}}", ctx["location"])
        .replace("{{VISIBLE_STATE}}", ctx["visible_state"] or "（当前空间暂无特别可视信息）")
        .replace("{{NPC_MEMORY_JSON}}", npc_memory_json)
        .replace("{{RECENT_DIALOGS_JSON}}", dialog_logs_json)
        .replace("{{PLAYER_INPUT}}", player_input.replace('"', '“'))  # 避免引号冲突
    )

    # 调用 LLM，解析为 DialogResponse
    resp = call_llm_structured(
        prompt=prompt,
        schema_model=DialogResponse,
        model=cfg.model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        cache_key=f"dialog::{npc_id}"
    )

    # 应用 npc_update 到 entities
    world = ctx["world"]
    entities = ctx["entities"]
    events = ctx["events"]

    apply_npc_update(entities, resp.npc_update)
    dump_json("data/entities.json", entities)

    # 记录对话日志
    append_jsonl("data/world_log.jsonl", {
        "event": "dialog",
        "npc_id": npc_id,
        "player_input": player_input,
        "npc_reply": resp.utterance_text,
        "npc_update": resp.npc_update.model_dump(),
    })

    print(f"[dialog] {npc_id}:", resp.utterance_text)
    return resp.utterance_text
