"""Tier 1 — Trend analysis for sequential lab values."""

from apps.api.engine.tier1.reference_ranges import get_reference_range


def compare_trend(
    test_id: str,
    current_value: float,
    previous_value: float,
    days_between: int = 90,
    age: int = 40,
    sex: str = "male",
) -> dict:
    """Compare current vs previous lab value and project trajectory.

    Returns {direction, delta, percent_change, rate_per_day, projected_days_to_critical}.
    """
    delta = current_value - previous_value
    if previous_value != 0:
        percent_change = round((delta / abs(previous_value)) * 100, 2)
    else:
        percent_change = 0.0

    rate_per_day = round(delta / max(days_between, 1), 4)

    if abs(delta) / max(abs(previous_value), 0.01) < 0.05:
        direction = "stable"
    elif delta > 0:
        direction = "up"
    else:
        direction = "down"

    # Project days to critical threshold
    projected_days_to_critical: float | None = None
    ref = get_reference_range(test_id, age, sex)
    if ref and rate_per_day != 0:
        if direction == "up" and ref.get("critical_high") is not None:
            remaining = ref["critical_high"] - current_value
            if remaining > 0 and rate_per_day > 0:
                projected_days_to_critical = round(remaining / rate_per_day, 1)
        elif direction == "down" and ref.get("critical_low") is not None:
            remaining = current_value - ref["critical_low"]
            if remaining > 0 and rate_per_day < 0:
                projected_days_to_critical = round(remaining / abs(rate_per_day), 1)

    return {
        "direction": direction,
        "delta": round(delta, 4),
        "percent_change": percent_change,
        "rate_per_day": rate_per_day,
        "projected_days_to_critical": projected_days_to_critical,
    }
