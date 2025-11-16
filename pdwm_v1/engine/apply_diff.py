# engine/apply_diff.py
from __future__ import annotations
from typing import Dict, Any, List
from engine.schemas import SpaceUpdate, NpcUpdate, EventProposal, UpdateList, Update
from engine.store import dump_json, append_jsonl

def _clip_importance(x: int) -> int:
    return max(1, min(3, x))

def apply_space_update(world: Dict[str, Any], upd: SpaceUpdate):
    sid = upd.space_id
    if sid not in world:
        # 忽略不存在的空间
        return
    space = world[sid]
    # 可视描述增量：简单拼接，你后面可以改成更精细的策略
    old_vis = space.get("visible_state", "")
    if old_vis:
        space["visible_state"] = (old_vis + " " + upd.visible_state_delta).strip()
    else:
        space["visible_state"] = upd.visible_state_delta

    # 潜在线索增删
    latent = space.get("latent_state", [])
    if latent is None:
        latent = []
    latent = list(latent)
    for op in upd.latent_state_ops:
        if op.op == "add" and op.cue not in latent:
            latent.append(op.cue)
        elif op.op == "remove" and op.cue in latent:
            latent.remove(op.cue)
    space["latent_state"] = latent

    # 重要度调整
    imp = space.get("importance", 1)
    space["importance"] = _clip_importance(imp + upd.importance_delta)

def apply_npc_update(entities: Dict[str, Any], upd: NpcUpdate):
    nid = upd.npc_id
    if nid not in entities:
        return
    npc = entities[nid]
    # 合并状态字典
    state_delta = upd.state_delta or {}
    for k, v in state_delta.items():
        npc[k] = v

    # 记忆写回：append 到 memory[]
    mem = npc.get("memory", [])
    if mem is None:
        mem = []
    mem = list(mem)
    mem.extend(upd.memory_write or [])
    npc["memory"] = mem

    # 重要度调整
    imp = npc.get("importance", 1)
    npc["importance"] = _clip_importance(imp + upd.importance_delta)

def apply_event_proposal(events: List[Dict[str, Any]], upd: EventProposal):
    # 简单策略：如果有同 id 事件则更新，否则 append
    for ev in events:
        if ev.get("id") == upd.event_id:
            ev["scope_spaces"] = upd.scope_spaces or ev.get("scope_spaces", [])
            ev["trigger_probability"] = upd.suggested_probability
            ev["possible_outcomes"] = upd.possible_outcomes or ev.get("possible_outcomes", [])
            return
    events.append({
        "id": upd.event_id,
        "scope_spaces": upd.scope_spaces,
        "trigger_probability": upd.suggested_probability,
        "possible_outcomes": upd.possible_outcomes,
        "latency": True
    })

def apply_updates(world: Dict[str, Any],
                  entities: Dict[str, Any],
                  events: List[Dict[str, Any]],
                  update_list: UpdateList,
                  source: str = "latent_update"):
    """统一应用一批更新，并写入日志。"""
    for upd in update_list.updates:
        if isinstance(upd, SpaceUpdate):
            apply_space_update(world, upd)
            append_jsonl("data/world_log.jsonl", {
                "event": source,
                "type": "space_update",
                "space_id": upd.space_id,
                "visible_state_delta": upd.visible_state_delta,
                "reasons": upd.reasons,
            })
        elif isinstance(upd, NpcUpdate):
            apply_npc_update(entities, upd)
            append_jsonl("data/world_log.jsonl", {
                "event": source,
                "type": "npc_update",
                "npc_id": upd.npc_id,
                "state_delta": upd.state_delta,
                "memory_write": upd.memory_write,
                "reasons": upd.reasons,
            })
        elif isinstance(upd, EventProposal):
            apply_event_proposal(events, upd)
            append_jsonl("data/world_log.jsonl", {
                "event": source,
                "type": "event_proposal",
                "event_id": upd.event_id,
                "scope_spaces": upd.scope_spaces,
                "prob": upd.suggested_probability,
                "justification": upd.justification,
            })

    # 应用完统一写回 JSON
    dump_json("data/world.json", world)
    dump_json("data/entities.json", entities)
    dump_json("data/events.json", events)
