from __future__ import annotations
import yaml
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Config:
    raw: Dict[str, Any]
    @property
    def model(self) -> str: return self.raw.get("model", "gpt-4o-mini")
    @property
    def temperature(self) -> float: return float(self.raw.get("temperature", 0.2))
    @property
    def max_tokens(self) -> int: return int(self.raw.get("max_tokens", 400))
    @property
    def seed(self) -> int: return int(self.raw.get("seed", 42))
    @property
    def context(self) -> Dict[str, Any]: return self.raw.get("context", {})
    @property
    def retry_on_schema_fail(self) -> int: return int(self.raw.get("retry_on_schema_fail", 1))
    @property
    def cache(self) -> bool: return bool(self.raw.get("cache", True))
    @property
    def max_updates_per_tick(self) -> int: return int(self.raw.get("max_updates_per_tick", 5))
    @property
    def max_updates_per_collapse(self) -> int: return int(self.raw.get("max_updates_per_collapse", 1))
    @property
    def init(self) -> Dict[str, Any]: return self.raw.get("init", {})

def load_config(path: str = "config.yaml") -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config(data)
