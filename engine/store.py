# engine/store.py
from __future__ import annotations
import json, os, time
from typing import Any, Dict

def load_json(path: str) -> Any:
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def dump_json(path: str, obj: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def append_jsonl(path: str, record: Dict[str, Any]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    record = dict(record)
    record.setdefault("ts", time.time())
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def snapshot(tag: str):
    # 轻量快照：把 world/entities/events 复制到 outputs/snapshots/<tag>/
    base = f"outputs/snapshots/{tag}"
    os.makedirs(base, exist_ok=True)
    for name in ["world.json", "entities.json", "events.json"]:
        src = f"data/{name}"
        if os.path.exists(src):
            with open(src, "r", encoding="utf-8") as f:
                content = f.read()
            with open(f"{base}/{name}", "w", encoding="utf-8") as f:
                f.write(content)
