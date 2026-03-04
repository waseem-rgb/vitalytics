"""Tier 3 — Specialist referral mapping."""

import json
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@lru_cache(maxsize=1)
def _load_advice() -> dict:
    path = DATA_DIR / "lifestyle_advice.json"
    with open(path) as f:
        return json.load(f)


def get_referral(pattern_id: str, severity: str = "moderate") -> dict | None:
    """Get specialist referral for a given pattern.

    Urgency may be escalated based on severity.
    """
    advice = _load_advice()
    pattern_advice = advice.get(pattern_id, {})
    referral = pattern_advice.get("specialist_referral")

    if referral is None:
        return None

    result = dict(referral)

    # Escalate urgency for critical/high severity
    if severity == "critical" and result.get("urgency") != "urgent":
        result["urgency"] = "urgent"
    elif severity == "high" and result.get("urgency") == "routine":
        result["urgency"] = "soon"

    return result
