"""Tier 3 — Further test recommendations."""

import json
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@lru_cache(maxsize=1)
def _load_advice() -> dict:
    path = DATA_DIR / "lifestyle_advice.json"
    with open(path) as f:
        return json.load(f)


def get_further_tests(pattern_id: str, existing_tests: set[str] | None = None) -> list[dict]:
    """Get recommended further tests for a pattern, filtering out already-tested items."""
    advice = _load_advice()
    pattern_advice = advice.get(pattern_id, {})
    all_tests = pattern_advice.get("further_tests", [])

    if not existing_tests:
        return all_tests

    # Normalize existing test names for matching
    existing_lower = {t.lower().replace(" ", "_").replace("-", "_") for t in existing_tests}

    filtered = []
    for test in all_tests:
        test_name_norm = test["test_name"].lower().replace(" ", "_").replace("-", "_")
        if test_name_norm not in existing_lower:
            filtered.append(test)

    return filtered
