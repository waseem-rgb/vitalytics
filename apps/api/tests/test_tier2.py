"""Tests for Tier 2 — Clinical pattern detection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from apps.api.engine.tier2.pattern_engine import evaluate_rules
from apps.api.engine.tier2.staging import get_ckd_stage, get_hba1c_stage, get_albuminuria_stage


class TestDemoCasePatterns:
    """Each demo case should produce expected patterns."""

    def test_case1_iron_deficiency_anemia(self):
        """32F — Hb 9.8, MCV 72, ferritin 6."""
        labs = {
            "hemoglobin": 9.8,
            "hematocrit": 30,
            "mcv": 72,
            "mch": 25,
            "mchc": 30,
            "rdw": 18,
            "ferritin": 6,
            "serum_iron": 35,
            "tibc": 420,
            "transferrin_saturation": 8,
            "wbc": 6.5,
            "platelets": 280000,
        }
        patterns = evaluate_rules(labs, 32, "female")
        pattern_ids = [p["id"] for p in patterns]
        assert "iron_deficiency_anemia" in pattern_ids

    def test_case2_ckd_hyperkalemia(self):
        """58M — creatinine 2.1, BUN 32, eGFR 38, ACR 180, K+ 5.4."""
        labs = {
            "creatinine": 2.1,
            "bun": 32,
            "egfr": 38,
            "urine_albumin_cr_ratio": 180,
            "potassium": 5.4,
            "sodium": 138,
            "calcium": 8.8,
            "phosphate": 5.2,
            "hemoglobin": 11.5,
            "bicarbonate": 20,
        }
        patterns = evaluate_rules(labs, 58, "male")
        pattern_ids = [p["id"] for p in patterns]
        assert "ckd_stage3_plus" in pattern_ids
        assert "hyperkalemia" in pattern_ids

    def test_case3_metabolic_syndrome(self):
        """45M — glucose 118, HbA1c 6.1, insulin 28, TG 240, HDL 34, LDL 155."""
        labs = {
            "fasting_glucose": 118,
            "hba1c": 6.1,
            "fasting_insulin": 28,
            "triglycerides": 240,
            "hdl": 34,
            "ldl": 155,
            "total_cholesterol": 265,
            "vldl": 48,
            "creatinine": 0.9,
            "alt": 35,
            "ast": 30,
        }
        patterns = evaluate_rules(labs, 45, "male")
        pattern_ids = [p["id"] for p in patterns]
        assert "prediabetes" in pattern_ids or "insulin_resistance" in pattern_ids
        assert "dyslipidemia" in pattern_ids

    def test_case4_hypothyroidism(self):
        """40F — TSH 12.5, FT4 0.6."""
        labs = {
            "tsh": 12.5,
            "free_t4": 0.6,
            "free_t3": 1.8,
            "hemoglobin": 11.2,
            "total_cholesterol": 280,
            "ldl": 180,
            "hdl": 55,
            "triglycerides": 160,
            "creatinine": 0.8,
        }
        patterns = evaluate_rules(labs, 40, "female")
        pattern_ids = [p["id"] for p in patterns]
        assert "primary_hypothyroidism" in pattern_ids

    def test_case5_liver_dyslipidemia(self):
        """50M — ALT 95, AST 78, ALP 120, bilirubin 1.8, glucose 135, HbA1c 7.2."""
        labs = {
            "alt": 95,
            "ast": 78,
            "alp": 120,
            "ggt": 85,
            "total_bilirubin": 1.8,
            "direct_bilirubin": 0.6,
            "albumin": 3.5,
            "fasting_glucose": 135,
            "hba1c": 7.2,
            "triglycerides": 280,
            "total_cholesterol": 260,
            "ldl": 160,
            "hdl": 38,
        }
        patterns = evaluate_rules(labs, 50, "male")
        pattern_ids = [p["id"] for p in patterns]
        # Should trigger liver patterns and diabetes
        assert any(pid in pattern_ids for pid in ["hepatocellular_injury", "mixed_liver"])
        assert "diabetes_mellitus" in pattern_ids


class TestStaging:
    def test_ckd_stages(self):
        assert get_ckd_stage(95)["stage"] == "G1"
        assert get_ckd_stage(70)["stage"] == "G2"
        assert get_ckd_stage(50)["stage"] == "G3a"
        assert get_ckd_stage(35)["stage"] == "G3b"
        assert get_ckd_stage(20)["stage"] == "G4"
        assert get_ckd_stage(10)["stage"] == "G5"

    def test_hba1c_stages(self):
        assert get_hba1c_stage(5.0)["stage"] == "normal"
        assert get_hba1c_stage(6.0)["stage"] == "prediabetes"
        assert get_hba1c_stage(6.8)["stage"] == "diabetes_controlled"
        assert get_hba1c_stage(7.5)["stage"] == "diabetes_suboptimal"
        assert get_hba1c_stage(8.5)["stage"] == "diabetes_poor"
        assert get_hba1c_stage(10.0)["stage"] == "diabetes_very_poor"

    def test_albuminuria_stages(self):
        assert get_albuminuria_stage(15)["stage"] == "A1"
        assert get_albuminuria_stage(100)["stage"] == "A2"
        assert get_albuminuria_stage(500)["stage"] == "A3"


class TestExclusions:
    def test_subclinical_excluded_by_overt_hypothyroidism(self):
        """subclinical_hypothyroidism should be excluded when primary_hypothyroidism matches."""
        labs = {"tsh": 12.5, "free_t4": 0.6}
        patterns = evaluate_rules(labs, 40, "female")
        pattern_ids = [p["id"] for p in patterns]
        assert "primary_hypothyroidism" in pattern_ids
        assert "subclinical_hypothyroidism" not in pattern_ids


# ---------------------------------------------------------------------------
# Real Predlabs case — 50-year-old male
# ---------------------------------------------------------------------------

PREDLABS_50M = {
    "hemoglobin": 15.8,
    "fasting_glucose": 244.77,
    "hba1c": 9.85,
    "triglycerides": 290.75,
    "hdl": 28.07,
    "ldl": 106.98,
    "total_cholesterol": 213.0,
    "vldl": 58.15,
    "alt": 78.43,
    "ast": 42.34,
    "alp": 215.53,
    "ggt": 93.7,
    "total_bilirubin": 0.82,
    "direct_bilirubin": 0.22,
    "albumin": 4.56,
    "total_protein": 7.82,
    "globulin": 3.26,
    "creatinine": 0.87,
    "bun": 10.2,
    "uric_acid": 5.62,
    "vitamin_d": 18.6,
    "aec": 510,
    "urine_protein": 2,  # 2+ (qualitative, encoded as numeric)
    "urine_glucose": 3,  # 3+ (qualitative, encoded as numeric)
    "sodium": 141,
    "potassium": 4.5,
    "chloride": 102,
    "calcium": 9.5,
    "wbc": 7.8,
    "platelets": 250000,
    "neutrophils": 4.5,
    "lymphocytes": 2.5,
}


class TestPredlabsCase:
    """Real Predlabs case — 50M with uncontrolled diabetes, dyslipidemia, liver injury."""

    def _get_patterns(self):
        return evaluate_rules(PREDLABS_50M, 50, "male")

    def _get_pattern_ids(self):
        return [p["id"] for p in self._get_patterns()]

    # 1. Diabetes patterns
    def test_predlabs_diabetes_patterns(self):
        """Fasting glucose 244.77 and HbA1c 9.85 → diabetes_mellitus + uncontrolled_diabetes."""
        pattern_ids = self._get_pattern_ids()
        assert "diabetes_mellitus" in pattern_ids
        assert "uncontrolled_diabetes" in pattern_ids

    # 2. Liver patterns
    def test_predlabs_liver_patterns(self):
        """ALT 78.43 is elevated → hepatocellular_injury."""
        pattern_ids = self._get_pattern_ids()
        assert "hepatocellular_injury" in pattern_ids

    # 3. Lipid patterns
    def test_predlabs_lipid_patterns(self):
        """TG 290.75 (>200) → severe_hypertriglyceridemia; high TG + low HDL → atherogenic_dyslipidemia."""
        pattern_ids = self._get_pattern_ids()
        assert "severe_hypertriglyceridemia" in pattern_ids
        assert "atherogenic_dyslipidemia" in pattern_ids

    # 4. NAFLD metabolic pattern
    def test_predlabs_nafld(self):
        """High ALT + high glucose + high TG → nafld_metabolic_pattern."""
        pattern_ids = self._get_pattern_ids()
        assert "nafld_metabolic_pattern" in pattern_ids

    # 5. Vitamin D insufficiency
    def test_predlabs_vitamin_d(self):
        """Vitamin D 18.6 (<30) → vitamin_d_insufficiency."""
        pattern_ids = self._get_pattern_ids()
        assert "vitamin_d_insufficiency" in pattern_ids

    # 6. Eosinophilia
    def test_predlabs_eosinophilia(self):
        """AEC 510 (>500) → mild_eosinophilia."""
        pattern_ids = self._get_pattern_ids()
        assert "mild_eosinophilia" in pattern_ids

    # 7. Glycosuria
    def test_predlabs_glycosuria(self):
        """Urine glucose 3+ (>0) → glycosuria."""
        pattern_ids = self._get_pattern_ids()
        assert "glycosuria" in pattern_ids

    # 8. Diabetic nephropathy signal
    def test_predlabs_nephropathy(self):
        """Urine protein 2+ (>0) AND HbA1c 9.85 (>6.5) → diabetic_nephropathy_signal."""
        pattern_ids = self._get_pattern_ids()
        assert "diabetic_nephropathy_signal" in pattern_ids

    # 9. Total pattern count
    def test_predlabs_total_pattern_count(self):
        """Should detect at least 10 distinct patterns for this complex case."""
        patterns = self._get_patterns()
        pattern_ids = [p["id"] for p in patterns]
        expected_minimum = {
            "diabetes_mellitus",
            "uncontrolled_diabetes",
            "hepatocellular_injury",
            "severe_hypertriglyceridemia",
            "atherogenic_dyslipidemia",
            "nafld_metabolic_pattern",
            "vitamin_d_insufficiency",
            "mild_eosinophilia",
            "glycosuria",
            "diabetic_nephropathy_signal",
        }
        missing = expected_minimum - set(pattern_ids)
        assert len(patterns) >= 10, (
            f"Expected >=10 patterns, got {len(patterns)}: {pattern_ids}"
        )
        assert not missing, f"Missing expected patterns: {missing}"

    # 10. Negative patterns — should NOT be detected
    def test_predlabs_negative_patterns(self):
        """Patterns that should NOT fire for this patient."""
        pattern_ids = self._get_pattern_ids()
        should_not_detect = [
            "iron_deficiency_anemia",
            "ckd_stage3_plus",
            "primary_hypothyroidism",
            "hyperkalemia",
        ]
        for pid in should_not_detect:
            assert pid not in pattern_ids, f"{pid} should NOT be detected"
