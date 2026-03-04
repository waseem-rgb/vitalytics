"""Tier 2 — Clinical rule definitions loader."""

import json
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@lru_cache(maxsize=1)
def load_rules() -> list[dict]:
    path = DATA_DIR / "clinical_rules.json"
    with open(path) as f:
        return json.load(f)


def get_rule(rule_id: str) -> dict | None:
    for rule in load_rules():
        if rule["id"] == rule_id:
            return rule
    return None


def get_rules_by_category(category: str) -> list[dict]:
    return [r for r in load_rules() if r.get("category", "").lower() == category.lower()]
