# engine/collapse.py
from __future__ import annotations
import json
from typing import Any, Dict, List

from engine.config import load_config
from engine.context import load_world_state, get_recent_logs
from engine.llm_executor import call_llm_structured
from engine.schemas import SpaceUpdate
from engine.apply_diff import apply_space_update
from engine.store import dump_json, append_jsonl

def _filter_space_logs(space_id: str, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从最近日志中筛选与该空间相关的部分（简单规则版）。"""
    filtered: List[Dict[str, Any]] = []
    for rec in logs:
        # 如果日志里显式有 space_id 字段 或 summary/备注中提到空间id，就留下
        if rec.get("space_id") == space_id or rec.get("player_location") == space_id:
            filtered.append(rec)
        else:
            # 简单兜底：在 summary 或 event 字段里字符串匹配
            text = json.dumps(rec, ensure_ascii=False)
            if space_id in text:
                filtered.append(rec)
    return filtered

def run_collapse(space_id: str):
    """
    玩家进入某空间：
    - 收集该空间的 visible_state + latent_state + 相关日志
    - 调用 LLM 生成一个 SpaceUpdate（显化）
    - 应用更新
    - 将该空间标记为 frozen=True
    """
    cfg = load_config()
    world, entities, events = load_world_state()

    if space_id not in world:
        print(f"[collapse] 空间 {space_id} 不存在。")
        return

    space = world[space_id]
    visible_state = space.get("visible_state", "")
    latent_state = space.get("latent_state", [])

    # 收集最近日志中与该空间相关的部分
    recent_k = cfg.context.get("recent_log_k", 10)
    logs = get_recent_logs(recent_k)
    space_logs = _filter_space_logs(space_id, logs)
    space_logs_json = json.dumps(space_logs, ensure_ascii=False, indent=2)

    # 构造 prompt
    with open("prompts/collapse.txt", "r", encoding="utf-8") as f:
        template = f.read()

    prompt = (
        template
        .replace("{{SPACE_ID}}", space_id)
        .replace("{{VISIBLE_STATE}}", visible_state or "（当前没有可视描述）")
        .replace("{{LATENT_STATE}}", json.dumps(latent_state, ensure_ascii=False, indent=2))
        .replace("{{SPACE_LOGS_JSON}}", space_logs_json)
    )

    # 调用 LLM，解析为 SpaceUpdate
    upd = call_llm_structured(
        prompt=prompt,
        schema_model=SpaceUpdate,
        model=cfg.model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        cache_key=f"collapse::{space_id}"
    )

    # 应用更新到 world
    apply_space_update(world, upd)

    # 标记该空间为 frozen（不再参与潜在更新）
    space = world[space_id]
    space["frozen"] = True

    # 写回 world.json
    dump_json("data/world.json", world)

    # 记录日志
    append_jsonl("data/world_log.jsonl", {
        "event": "collapse",
        "space_id": space_id,
        "visible_state_delta": upd.visible_state_delta,
        "latent_state_ops": [op.model_dump() for op in upd.latent_state_ops],
        "importance_delta": upd.importance_delta,
        "reasons": upd.reasons,
    })

    print(f"[collapse] 空间 {space_id} 已坍缩显化并冻结。")
    print(f"  新增可视描述：{upd.visible_state_delta}")
