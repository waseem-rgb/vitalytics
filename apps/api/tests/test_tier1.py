"""Tests for Tier 1 — Value interpretation engine."""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from apps.api.engine.tier1.interpreter import interpret_value, interpret_panel, normalize_unit
from apps.api.engine.tier1.trend import compare_trend


class TestNormalizeUnit:
    def test_hemoglobin_gl_to_gdl(self):
        # 120 g/L * 0.1 = 12.0 g/dL
        result = normalize_unit("hemoglobin", 120, "g/L")
        assert abs(result - 12.0) < 0.01

    def test_unknown_unit_returns_original(self):
        result = normalize_unit("hemoglobin", 15.0, "unknown_unit")
        assert result == 15.0

    def test_unknown_test_returns_original(self):
        result = normalize_unit("nonexistent_test", 100, "mg/dL")
        assert result == 100


class TestInterpretValue:
    def test_normal_hemoglobin_male(self):
        result = interpret_value("hemoglobin", 15.0, 40, "male")
        assert result["status"] == "normal"
        assert result["flag_color"] == "green"
        assert result["severity_score"] == 0

    def test_low_hemoglobin_female(self):
        result = interpret_value("hemoglobin", 9.8, 32, "female")
        assert result["status"] == "low"
        assert result["flag_color"] == "amber"
        assert result["severity_score"] > 0

    def test_critical_low_hemoglobin(self):
        result = interpret_value("hemoglobin", 5.0, 40, "male")
        assert result["status"] == "critical_low"
        assert result["flag_color"] == "red"
        assert result["severity_score"] == 10

    def test_high_tsh(self):
        result = interpret_value("tsh", 12.5, 40, "female")
        assert result["status"] in ("high", "critical_high")
        assert result["flag_color"] in ("amber", "red")

    def test_normal_sodium(self):
        result = interpret_value("sodium", 140, 50, "male")
        assert result["status"] == "normal"

    def test_unknown_test(self):
        result = interpret_value("nonexistent", 100, 40, "male")
        assert result["status"] == "unknown"


class TestInterpretPanel:
    """Test the IDA demo case panel."""

    def test_ida_case(self):
        labs = {
            "hemoglobin": 9.8,
            "mcv": 72,
            "ferritin": 6,
            "serum_iron": 35,
            "tibc": 420,
        }
        results = interpret_panel(labs, 32, "female")
        assert "hemoglobin" in results
        assert results["hemoglobin"]["status"] == "low"
        assert results["mcv"]["status"] == "low"
        assert results["ferritin"]["status"] == "low"

    def test_ckd_case(self):
        labs = {
            "creatinine": 2.1,
            "bun": 32,
            "egfr": 38,
            "potassium": 5.4,
        }
        results = interpret_panel(labs, 58, "male")
        assert results["creatinine"]["status"] in ("high", "critical_high")
        assert results["egfr"]["status"] == "low"

    def test_skips_none_values(self):
        labs = {"hemoglobin": 15.0, "mcv": None}
        results = interpret_panel(labs, 40, "male")
        assert "hemoglobin" in results
        assert "mcv" not in results


class TestTrend:
    def test_rising_trend(self):
        result = compare_trend("creatinine", 2.1, 1.2, 90, 58, "male")
        assert result["direction"] == "up"
        assert result["delta"] > 0
        assert result["percent_change"] > 0

    def test_falling_trend(self):
        result = compare_trend("hemoglobin", 9.8, 12.0, 90, 32, "female")
        assert result["direction"] == "down"
        assert result["delta"] < 0

    def test_stable_trend(self):
        result = compare_trend("sodium", 140, 139.5, 90, 50, "male")
        assert result["direction"] == "stable"

    def test_projected_days_to_critical(self):
        # Hemoglobin dropping toward critical
        result = compare_trend("hemoglobin", 8.0, 10.0, 30, 40, "male")
        assert result["direction"] == "down"
        # Should project days until critical_low (7.0)
        if result["projected_days_to_critical"] is not None:
            assert result["projected_days_to_critical"] > 0
