#!/usr/bin/env python3
"""Seed reference ranges and verify data integrity."""

import sys
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from apps.api.app.core.config import DATA_DIR


def main():
    print("Verifying Vitalytics data files...")
    print("=" * 50)

    # Check reference ranges
    ref_path = DATA_DIR / "reference_ranges.json"
    if ref_path.exists():
        with open(ref_path) as f:
            ranges = json.load(f)
        print(f"  reference_ranges.json: {len(ranges)} tests")
    else:
        print("  ERROR: reference_ranges.json not found!")

    # Check clinical rules
    rules_path = DATA_DIR / "clinical_rules.json"
    if rules_path.exists():
        with open(rules_path) as f:
            rules = json.load(f)
        print(f"  clinical_rules.json:   {len(rules)} rules")
    else:
        print("  ERROR: clinical_rules.json not found!")

    # Check lifestyle advice
    advice_path = DATA_DIR / "lifestyle_advice.json"
    if advice_path.exists():
        with open(advice_path) as f:
            advice = json.load(f)
        print(f"  lifestyle_advice.json: {len(advice)} patterns")
    else:
        print("  ERROR: lifestyle_advice.json not found!")

    print("=" * 50)
    print("Data verification complete.")


if __name__ == "__main__":
    main()
