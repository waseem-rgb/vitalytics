"""Tier 1 — Value interpretation engine."""

from apps.api.engine.tier1.reference_ranges import get_range, get_reference_range


def normalize_unit(test_id: str, value: float, from_unit: str) -> float:
    """Convert value from from_unit to the standard unit for test_id."""
    entry = get_range(test_id)
    if entry is None:
        return value
    conversions = entry.get("conversions", {})
    factor = conversions.get(from_unit)
    if factor is None:
        return value
    return round(value * factor, 4)


def interpret_value(
    test_id: str, value: float, age: int, sex: str
) -> dict:
    """Interpret a single lab value against reference ranges.

    Returns {status, value, unit, reference_range, plain_text, severity_score, flag_color}.
    """
    ref = get_reference_range(test_id, age, sex)
    entry = get_range(test_id)

    if ref is None or entry is None:
        return {
            "status": "unknown",
            "value": value,
            "unit": "",
            "reference_range": None,
            "plain_text": f"No reference range available for {test_id}.",
            "severity_score": 0,
            "flag_color": "gray",
        }

    low = ref["low"]
    high = ref["high"]
    crit_low = ref.get("critical_low")
    crit_high = ref.get("critical_high")
    unit = ref["unit"]
    plain = entry.get("plain_language", {})

    # Determine status
    if crit_low is not None and value <= crit_low:
        status = "critical_low"
        severity = 10
        color = "red"
    elif crit_high is not None and value >= crit_high:
        status = "critical_high"
        severity = 10
        color = "red"
    elif low is not None and value < low:
        status = "low"
        # Scale severity 1-6 based on how far below
        if low > 0:
            pct_below = (low - value) / low
            severity = min(6, max(1, round(pct_below * 10)))
        else:
            severity = 3
        color = "amber"
    elif high is not None and value > high:
        status = "high"
        if high > 0:
            pct_above = (value - high) / high
            severity = min(6, max(1, round(pct_above * 10)))
        else:
            severity = 3
        color = "amber"
    else:
        status = "normal"
        severity = 0
        color = "green"

    plain_text = plain.get(status, f"Your {entry.get('name', test_id)} is {status}.")

    return {
        "status": status,
        "value": value,
        "unit": unit,
        "reference_range": {"low": low, "high": high},
        "plain_text": plain_text,
        "severity_score": severity,
        "flag_color": color,
    }


def interpret_qualitative(test_id: str, value, age: int, sex: str) -> dict:
    """Interpret a qualitative lab value (e.g., urine_protein: '2+')."""
    entry = get_range(test_id)
    if entry is None:
        return {
            "status": "unknown",
            "value": value,
            "unit": "qualitative",
            "reference_range": None,
            "plain_text": f"No reference available for {test_id}.",
            "severity_score": 0,
            "flag_color": "gray",
        }

    normal_values = entry.get("normal_values", ["negative"])
    plain = entry.get("plain_language", {})
    str_val = str(value).lower().strip()

    is_normal = str_val in [v.lower() for v in normal_values] or str_val in ("0", "0.0")

    if is_normal:
        return {
            "status": "normal",
            "value": value,
            "unit": "qualitative",
            "reference_range": {"low": None, "high": None, "normal": ", ".join(normal_values)},
            "plain_text": plain.get("normal", f"{entry.get('name', test_id)} is normal."),
            "severity_score": 0,
            "flag_color": "green",
        }
    else:
        # Determine severity from plus count
        import re
        plus_match = re.search(r"(\d)\+", str(value))
        if plus_match:
            plus_count = int(plus_match.group(1))
            severity = min(8, plus_count * 2)
        else:
            severity = 3
        return {
            "status": "high",
            "value": value,
            "unit": "qualitative",
            "reference_range": {"low": None, "high": None, "normal": ", ".join(normal_values)},
            "plain_text": plain.get("high", f"{entry.get('name', test_id)} is abnormal."),
            "severity_score": severity,
            "flag_color": "red" if severity >= 6 else "amber",
        }


def interpret_panel(
    lab_results: dict, age: int, sex: str
) -> dict:
    """Interpret all lab results in a panel.

    lab_results: {test_id: value, ...}
    Returns: {test_id: interpretation_dict, ...}
    """
    # Qualitative tests that should not be cast to float
    QUALITATIVE_TESTS = {
        "urine_protein", "urine_glucose", "urine_ketones",
        "urine_casts", "urine_bacteria",
    }

    results = {}
    for test_id, value in lab_results.items():
        if value is None:
            continue

        entry = get_range(test_id)
        is_qual = (entry and entry.get("qualitative")) or test_id in QUALITATIVE_TESTS

        if is_qual:
            results[test_id] = interpret_qualitative(test_id, value, age, sex)
        else:
            try:
                val = float(value)
            except (TypeError, ValueError):
                continue
            results[test_id] = interpret_value(test_id, val, age, sex)
    return results
