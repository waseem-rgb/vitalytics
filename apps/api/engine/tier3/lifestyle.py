"""Tier 3 — Lifestyle recommendations."""

import json
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@lru_cache(maxsize=1)
def _load_advice() -> dict:
    path = DATA_DIR / "lifestyle_advice.json"
    with open(path) as f:
        return json.load(f)


def get_lifestyle_plan(pattern_ids: list[str], age: int = 40, sex: str = "male") -> dict:
    """Build a deduplicated combined lifestyle plan from multiple patterns."""
    advice = _load_advice()

    diet_set: list[str] = []
    exercise_set: list[dict] = []
    sleep_set: list[str] = []
    stress_set: list[str] = []
    weight_items: list[str] = []
    smoking_items: list[str] = []

    seen_diet: set[str] = set()
    seen_exercise: set[str] = set()
    seen_sleep: set[str] = set()
    seen_stress: set[str] = set()

    for pid in pattern_ids:
        pa = advice.get(pid, {})
        lifestyle = pa.get("lifestyle", {})

        for item in lifestyle.get("diet", []):
            if isinstance(item, str) and item not in seen_diet:
                seen_diet.add(item)
                diet_set.append(item)

        for item in lifestyle.get("exercise", []):
            key = item.get("type", str(item)) if isinstance(item, dict) else str(item)
            if key not in seen_exercise:
                seen_exercise.add(key)
                exercise_set.append(item)

        for item in lifestyle.get("sleep", []):
            if isinstance(item, str) and item not in seen_sleep:
                seen_sleep.add(item)
                sleep_set.append(item)

        for item in lifestyle.get("stress", []):
            if isinstance(item, str) and item not in seen_stress:
                seen_stress.add(item)
                stress_set.append(item)

        w = lifestyle.get("weight")
        if w and w not in weight_items:
            weight_items.append(w)

        s = lifestyle.get("smoking")
        if s and s not in smoking_items:
            smoking_items.append(s)

    return {
        "diet": diet_set,
        "exercise": exercise_set,
        "sleep": sleep_set,
        "stress": stress_set,
        "weight": weight_items if weight_items else None,
        "smoking": smoking_items if smoking_items else None,
    }
