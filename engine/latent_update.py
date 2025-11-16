# engine/latent_update.py
from __future__ import annotations
import json
from engine.config import load_config
from engine.context import load_world_state, get_recent_logs, build_candidates
from engine.llm_executor import call_llm_structured
from engine.schemas import UpdateList
from engine.apply_diff import apply_updates

def run_latent_tick():
    """
    执行一次“潜在世界更新”：
    - 选出候选对象（目前是全 world/entities）
    - 取最近日志
    - 调用大模型生成 updates
    - 应用 updates 写回世界
    """
    cfg = load_config()
    world, entities, events = load_world_state()

    # 构造候选对象 & 最近日志 JSON 字符串
    candidates = build_candidates(world, entities)
    recent_k = cfg.context.get("recent_log_k", 10)
    logs = get_recent_logs(recent_k)

    candidates_json = json.dumps(candidates, ensure_ascii=False, indent=2)
    logs_json = json.dumps(logs, ensure_ascii=False, indent=2)

    # 读取 prompt 模板
    with open("prompts/latent_update.txt", "r", encoding="utf-8") as f:
        template = f.read()

    prompt = (
        template
        .replace("{{CANDIDATES_JSON}}", candidates_json)
        .replace("{{RECENT_LOGS_JSON}}", logs_json)
        .replace("{{RECENT_K}}", str(recent_k))
        .replace("{{MAX_UPDATES}}", str(cfg.max_updates_per_tick))
    )

    # 调用大模型，强制解析为 UpdateList
    update_list = call_llm_structured(
        prompt=prompt,
        schema_model=UpdateList,
        model=cfg.model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        cache_key="latent_tick"
    )

    if not update_list.updates:
        print("[latent] 无更新。")
        return

    # 应用更新，写回 world/entities/events，并写log
    apply_updates(world, entities, events, update_list, source="latent_update")
    print(f"[latent] 已应用 {len(update_list.updates)} 个更新。")
