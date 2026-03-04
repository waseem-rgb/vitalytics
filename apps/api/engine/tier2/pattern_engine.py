"""Tier 2 — Pattern matching engine.

Evaluates clinical rules against lab results to detect clinical patterns.
Handles both numeric and qualitative (urine_protein, urine_glucose) values.
"""

from apps.api.engine.tier1.interpreter import interpret_value
from apps.api.engine.tier2.clinical_rules import load_rules


def _to_numeric(value) -> float | None:
    """Try to convert a value to float. Handles qualitative urine values."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            pass
    return None


def matches_condition(condition: dict, lab_results: dict, age: int, sex: str) -> bool:
    """Check if a single condition is met by the lab results."""
    test_id = condition["test"]
    if test_id not in lab_results:
        return False

    raw_value = lab_results[test_id]
    direction = condition.get("direction", "")

    # For qualitative tests (urine_protein, urine_glucose, etc.)
    # Values are stored as numbers: 0 = negative, 1+ = 1, 2+ = 2, etc.
    numeric_val = _to_numeric(raw_value)
    if numeric_val is None:
        # Pure string value — check if "high" means present/positive
        if direction == "high":
            str_val = str(raw_value).lower()
            return str_val not in ("negative", "absent", "nil", "none", "0")
        return False

    value = numeric_val

    # Qualitative tests like urine_protein: any value > 0 means "high" (abnormal)
    is_qualitative = test_id in (
        "urine_protein", "urine_glucose", "urine_ketones",
        "urine_casts", "urine_bacteria",
    )

    # Threshold-based conditions
    if "threshold" in condition:
        threshold = condition["threshold"]
        if direction == "high":
            return value >= threshold
        elif direction == "low":
            return value <= threshold
        return False

    # Range-based (borderline)
    if direction == "borderline_high":
        tl = condition.get("threshold_low")
        th = condition.get("threshold_high")
        if tl is not None and th is not None:
            return tl <= value <= th
        return False

    # For qualitative tests, "high" means any positive value
    if is_qualitative:
        if direction == "high":
            return value > 0
        elif direction == "low" or direction == "normal":
            return value == 0
        return False

    # Use the interpreter for standard numeric tests
    interp = interpret_value(test_id, value, age, sex)
    status = interp["status"]

    # Direction-based
    if direction == "low":
        return status in ("low", "critical_low")
    elif direction == "high":
        return status in ("high", "critical_high")
    elif direction == "normal":
        return status == "normal"
    elif direction == "high_or_normal":
        return status in ("normal", "high", "critical_high")

    return False


def evaluate_rules(lab_results: dict, age: int, sex: str) -> list[dict]:
    """Evaluate all clinical rules against the lab results.

    Returns list of MatchedPattern dicts sorted by severity.
    """
    rules = load_rules()
    matched_patterns: list[dict] = []
    matched_ids: set[str] = set()

    # First pass: find all matches
    candidates = []
    for rule in rules:
        conditions = rule.get("conditions", [])
        min_match = rule.get("min_match", len(conditions))

        matched_conditions = []
        for cond in conditions:
            if matches_condition(cond, lab_results, age, sex):
                matched_conditions.append(cond)

        if len(matched_conditions) >= min_match:
            confidence = calculate_confidence(rule, len(matched_conditions), len(conditions))
            candidates.append({
                "id": rule["id"],
                "name": rule["name"],
                "category": rule.get("category", ""),
                "severity": rule.get("severity", "low"),
                "interpretation": rule.get("interpretation", ""),
                "harrison_ref": rule.get("harrison_ref", ""),
                "confidence": confidence,
                "matched_criteria": f"{len(matched_conditions)}/{len(conditions)}",
                "matched_count": len(matched_conditions),
                "total_conditions": len(conditions),
                "exclude_if": rule.get("exclude_if", []),
            })

    # Sort by severity for exclusion logic (higher severity wins)
    severity_order = {"critical": 4, "high": 3, "moderate": 2, "low": 1}
    candidates.sort(key=lambda c: severity_order.get(c["severity"], 0), reverse=True)

    # Second pass: apply exclusions
    for candidate in candidates:
        matched_ids.add(candidate["id"])

    for candidate in candidates:
        excluded = False
        for excl_id in candidate.get("exclude_if", []):
            if excl_id in matched_ids:
                excluded = True
                break
        if not excluded:
            matched_patterns.append(candidate)

    return matched_patterns


def calculate_confidence(rule: dict, matched_count: int, total_conditions: int) -> float:
    """Calculate confidence score for a pattern match."""
    if total_conditions == 0:
        return 0.0
    base = matched_count / total_conditions
    # Boost for exact match
    if matched_count == total_conditions:
        base = min(1.0, base * 1.1)
    return round(base, 2)
