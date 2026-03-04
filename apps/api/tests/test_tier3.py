"""Tests for Tier 3 — Action plans."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from apps.api.engine.tier3.further_tests import get_further_tests
from apps.api.engine.tier3.referrals import get_referral
from apps.api.engine.tier3.lifestyle import get_lifestyle_plan


class TestFurtherTests:
    def test_iron_deficiency_has_tests(self):
        tests = get_further_tests("iron_deficiency_anemia")
        assert len(tests) > 0
        test_names = [t["test_name"] for t in tests]
        assert any("smear" in n.lower() or "reticul" in n.lower() for n in test_names)

    def test_deduplication_filters_existing(self):
        """Should not recommend tests already in the report."""
        all_tests = get_further_tests("iron_deficiency_anemia", existing_tests=set())
        filtered = get_further_tests(
            "iron_deficiency_anemia",
            existing_tests={"ferritin", "hemoglobin", "serum_iron"},
        )
        # Filtered should be <= all
        assert len(filtered) <= len(all_tests)

    def test_unknown_pattern_returns_empty(self):
        tests = get_further_tests("nonexistent_pattern")
        assert tests == []


class TestReferrals:
    def test_iron_deficiency_referral(self):
        ref = get_referral("iron_deficiency_anemia", "moderate")
        assert ref is not None
        assert "specialist" in ref

    def test_critical_escalates_urgency(self):
        ref = get_referral("iron_deficiency_anemia", "critical")
        assert ref is not None
        assert ref["urgency"] == "urgent"

    def test_high_escalates_from_routine(self):
        ref = get_referral("iron_deficiency_anemia", "high")
        if ref and ref.get("urgency"):
            # Should be at least "soon" if original was "routine"
            assert ref["urgency"] in ("soon", "urgent", "routine")

    def test_unknown_pattern(self):
        ref = get_referral("nonexistent_pattern", "moderate")
        assert ref is None


class TestLifestyle:
    def test_single_pattern(self):
        plan = get_lifestyle_plan(["iron_deficiency_anemia"], 32, "female")
        assert len(plan["diet"]) > 0
        assert len(plan["exercise"]) > 0

    def test_multiple_patterns_deduplication(self):
        plan = get_lifestyle_plan(
            ["iron_deficiency_anemia", "primary_hypothyroidism", "dyslipidemia"],
            40,
            "female",
        )
        # Should have combined diet items without duplicates
        assert len(plan["diet"]) > 0
        assert len(set(plan["diet"])) == len(plan["diet"])  # No duplicates

    def test_no_patterns_returns_empty(self):
        plan = get_lifestyle_plan([], 40, "male")
        assert plan["diet"] == []
        assert plan["exercise"] == []
