# engine/context.py
from __future__ import annotations
from typing import List, Dict, Any
from engine.store import load_json
import os, json

LOG_PATH = "data/world_log.jsonl"

def load_world_state():
    """加载当前 world/entities/events 三件套。"""
    world = load_json("data/world.json")
    entities = load_json("data/entities.json")
    events = load_json("data/events.json")
    return world, entities, events

def get_recent_logs(k: int) -> List[Dict[str, Any]]:
    """从 world_log.jsonl 取最近 k 条日志（从后往前读）。"""
    if not os.path.exists(LOG_PATH):
        return []
    lines: List[str] = []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    lines = lines[-k:]
    logs: List[Dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return logs

def build_candidates(world: Dict[str, Any],
                     entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    构造给 LLM 的候选对象摘要：
    - spaces: [{id, importance, status}, ...]，跳过 frozen 的空间
    - npcs:   [{id, importance, location, role}, ...]
    """
    spaces = []
    for sid, s in world.items():
        if s.get("frozen", False):
            continue  # 已坍缩冻结的空间，不再做潜在更新
        spaces.append({
            "id": sid,
            "type": "space",
            "importance": s.get("importance", 1),
            "status": s.get("status", ""),
        })

    npcs = []
    for nid, e in entities.items():
        npcs.append({
            "id": nid,
            "type": "npc",
            "importance": e.get("importance", 1),
            "location": e.get("location", ""),
            "role": e.get("role", ""),
        })

    return {"spaces": spaces, "npcs": npcs}
