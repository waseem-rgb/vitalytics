"""Tests for the Indian lab PDF parser using actual Predlabs raw text."""

import sys
from pathlib import Path

# Ensure project root is on path
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from apps.api.engine.ocr.indian_lab_parser import (
    _extract_values_from_page,
    _extract_qualitative,
    _extract_patient_info,
)

# ──────────────────────────────────────────────────────────────
# Actual raw text from a 24-page Predlabs report (PyMuPDF output)
# ──────────────────────────────────────────────────────────────

PAGE_PATIENT = """
Patient Name : DR WASEEM AFSAR
Age / Sex : 50 Years / Male
Registration On : 15 Feb, 2026
Sample ID : PL-123456
Reported On : 16 Feb, 2026
"""

PAGE_HBAIC = """GLYCOSYLATED HEMOGLOBIN - HBA1C
HbA1c 9.85 % Below 6.0% - Normal Value
6.0% - 7.0% - Good Control
7.0% - 8.0% - Fair Control
8.0% - 10% - Unsatisfactory Control
Above 10% - Poor Control
HPLC Method
AVERAGE BLOOD GLUCOSE
(ABG)
236.00 mg/dl -
"""

PAGE_FASTING_GLUCOSE = """GLUCOSE - FASTING
Glucose Fasting
(Plasma)
244.77 mg/dl Non-Diabetic(Fasting) \u2264100
Pre-Diabetic : 100 - 125
Diabetic : >126
Hexokinase
"""

PAGE_LFT = """LIVER FUNCTION TEST SERUM (WITH GGT)
Bilirubin Total - serum 0.75 mg/dL 0.3 - 1.2 Diazo Salt Method
Bilirubin Direct - serum 0.13 mg/dL 0 - 0.2 Diazo Salt Method
Bilirubin Indirect - serum 0.62 mg/dL 0.3 - 1.0 Calculated
SGOT (AST) - serum 42.34 U/L 13 - 33 IFCC
SGPT (ALT) - serum 78.43 U/L Male 8-42 IFCC with P5P
SGOT/SGPT Ratio- serum 0.54 % <2.0 Calculated
Alkaline Phosphatase - serum 215.53 U/L 40-150 AMP optimised
Protein Total - serum 7.47 g/dL 6.7 - 8.3 Biuret Method
Albumin - serum 4.15 g/dL 4.0 - 5.0 Bromo-Cresol Green
Globulin 3.32 g/dL 2.0 - 4.1 Calculated
A/G Ratio -serum 1.25 1.0 - 2.1 Calculated
GGTP - Gamma GT - serum 93.7 U/L 10-47 IFCC Reference Method
"""

PAGE_LIPID = """LIPID PROFILE
Total Cholesterol - serum 154.95 mg/dl Desirable : < 200
Triglycerides - serum 290.75 mg/dl Normal : < 150
HDL Cholesterol -serum 28.07 mg/dl < 35 Low
Non HDL Cholesterolserum 126.88 mg/dl Desirable : < 130
LDL Cholesterol -serum 68.73 mg/dL Very high Risk : >= 190
VLDL Cholesterol -serum 58.15 mg/dl Below 30 Calculated
"""

PAGE_CBC = """COMPLETE BLOOD COUNT - CBC
Haemoglobin 15.8 gm/dl 13.5-18.0 Cyanide Free Method
Total WBC Count 7.52 10^3 / uL 4.0 - 11 Elec. Impedance
RBC Count 5.43 10^6 / uL 4.5 - 5.5 Elec. Impedence
Haematocrit/Packed Cell Volume 50.2 % 40 - 50 Calculated
MCV 92.5 fL 80 - 100
MCH 29 pg 27 - 32
MCHC 31.5 gm/dl 31.5 - 34.5
RDW-SD 41.6 fL 36 - 56
RDW-CV 12.5 % 11.5 - 14.5
Platelet Count 230 10^3 / uL 150 - 450
"""

PAGE_DIFF = """DIFFERENTIAL COUNT
Neutrophils 46.1 % 40 - 75
Lymphocytes 38.2 % 20 - 40
Monocytes 7.9 % 2 - 9
Eosinophil 6.8 % 1 - 7
Basophils 1 % 0 - 1
Absolute Neutrophils Count 3.47 10^3/uL 1.5 - 8
Absolute Lymphocyte Count 2.87 10^3/uL 1.5 - 8
Absolute Eosinophil Count 0.51 10^3/uL 0.04 - 0.4
Absolute Basophils Count 0.08 10^3/uL 0 - 0.2
Absolute Monocyte Count 0.59 10^3/uL 0.2 - 1.0
"""

PAGE_KFT = """KIDNEY BASIC SCREEN - KFT
Serum Urea 33.44 mg/dl 12.8 - 42.8
BUN 15.63 mg/dl 6 - 20
Serum Creatinine 0.76 mg/dl Male : 0.6 - 1.1
Serum Uric acid 4.68 mg/dl Male : 4.0 - 7.0
BUN / Creatinine Ratio 20.57
Urea / Creatinine Ratio 44
eGFR 123.29 70 - 200
"""

PAGE_THYROID = """THYROID PROFILE : T3,T4,TSH
TOTAL TRIIODOTHYRONINE (T3) 1.33 ng/mL 0.763 - 2.208
TOTAL THYROXINE (T4) 7.95 \u00b5g/dL 4.5 - 13
THYROID STIMULATING HORMONE (TSH) 3.52 \u00b5IU/mL 0.3 - 4.5
"""

PAGE_VITB12 = """VITAMIN - B12
Vitamin B12 670 pg/mL 192-827 pg/mL
"""

PAGE_VITD = """VITAMIN - D
Vitamin D Total-25 Hydroxy (Serum) 18.6 ng/mL Deficiency <10 ng/mL;
"""

PAGE_IRON = """IRON
IRON 87.81 \u00b5g/dL 37 - 170
"""

PAGE_CALCIUM = """CALCIUM - SERUM
CALCIUM - serum 9.5 mg/dl 8.5 - 10.3
"""

PAGE_URINE = """CUE - COMPLETE URINE ANALYSIS
Physical Examination
Colour Pale Yellow
Appearance Clear
Specific Gravity 1.030 1.005-1.030
pH 6.0 5.0 - 8.0
Chemical Examination
Protein Present (++) Negative
Glucose Present (+++) Negative
Ketones Negative Negative
Bile Salt Negative Negative
Bile Pigment Negative Negative
"""

PAGE_TUMOR = """ALPHA FETO PROTEIN (AFP) 3.32 IU/ml \u22646.514
CEA 3.63 ng/mL (Non-Smoker 14-81 \u22645.093)
CA -19.9 10.7 U/mL < 28
CA -15.3 12.4 U/mL < 28
TOTAL PSA (Prostate - Specific Antigen) 0.938 ng/mL 0 - 4
"""


class TestPredlabsParser(unittest.TestCase):
    """Test parser against actual Predlabs raw text."""

    def _get_values(self, text: str, page: int = 1) -> dict[str, float]:
        """Helper: extract values and return as dict."""
        found, _ = _extract_values_from_page(text, page)
        return {test_id: p.value for test_id, p in found}

    # ── Patient Info ──

    def test_patient_info(self):
        info = _extract_patient_info(PAGE_PATIENT)
        self.assertEqual(info["name"], "DR WASEEM AFSAR")
        self.assertEqual(info["age"], 50)
        self.assertEqual(info["sex"], "male")

    # ── HbA1c / Diabetes ──

    def test_hba1c(self):
        vals = self._get_values(PAGE_HBAIC)
        self.assertIn("hba1c", vals)
        self.assertAlmostEqual(vals["hba1c"], 9.85)

    def test_avg_blood_glucose(self):
        vals = self._get_values(PAGE_HBAIC)
        self.assertIn("avg_blood_glucose", vals)
        self.assertAlmostEqual(vals["avg_blood_glucose"], 236.00)

    def test_fasting_glucose(self):
        vals = self._get_values(PAGE_FASTING_GLUCOSE)
        self.assertIn("fasting_glucose", vals)
        self.assertAlmostEqual(vals["fasting_glucose"], 244.77)

    # ── LFT ──

    def test_lft_values(self):
        vals = self._get_values(PAGE_LFT)
        self.assertAlmostEqual(vals["total_bilirubin"], 0.75)
        self.assertAlmostEqual(vals["direct_bilirubin"], 0.13)
        self.assertAlmostEqual(vals["indirect_bilirubin"], 0.62)
        self.assertAlmostEqual(vals["ast"], 42.34)
        self.assertAlmostEqual(vals["alt"], 78.43)
        self.assertAlmostEqual(vals["ast_alt_ratio"], 0.54)
        self.assertAlmostEqual(vals["alp"], 215.53)
        self.assertAlmostEqual(vals["total_protein"], 7.47)
        self.assertAlmostEqual(vals["albumin"], 4.15)
        self.assertAlmostEqual(vals["globulin"], 3.32)
        self.assertAlmostEqual(vals["ag_ratio"], 1.25)
        self.assertAlmostEqual(vals["ggt"], 93.7)

    # ── Lipid ──

    def test_lipid_values(self):
        vals = self._get_values(PAGE_LIPID)
        self.assertAlmostEqual(vals["total_cholesterol"], 154.95)
        self.assertAlmostEqual(vals["triglycerides"], 290.75)
        self.assertAlmostEqual(vals["hdl"], 28.07)
        self.assertAlmostEqual(vals["non_hdl_cholesterol"], 126.88)
        self.assertAlmostEqual(vals["ldl"], 68.73)
        self.assertAlmostEqual(vals["vldl"], 58.15)

    # ── CBC ──

    def test_cbc_values(self):
        vals = self._get_values(PAGE_CBC)
        self.assertAlmostEqual(vals["hemoglobin"], 15.8)
        self.assertAlmostEqual(vals["wbc"], 7.52)
        self.assertAlmostEqual(vals["rbc"], 5.43)
        self.assertAlmostEqual(vals["hematocrit"], 50.2)
        self.assertAlmostEqual(vals["mcv"], 92.5)
        self.assertAlmostEqual(vals["mch"], 29)
        self.assertAlmostEqual(vals["mchc"], 31.5)
        self.assertAlmostEqual(vals["rdw"], 12.5)
        self.assertAlmostEqual(vals["platelets"], 230)

    # ── Differential ──

    def test_diff_values(self):
        vals = self._get_values(PAGE_DIFF)
        self.assertAlmostEqual(vals["neutrophils_pct"], 46.1)
        self.assertAlmostEqual(vals["lymphocytes_pct"], 38.2)
        self.assertAlmostEqual(vals["monocytes_pct"], 7.9)
        self.assertAlmostEqual(vals["eosinophils_pct"], 6.8)
        self.assertAlmostEqual(vals["basophils_pct"], 1)
        self.assertAlmostEqual(vals["anc"], 3.47)
        self.assertAlmostEqual(vals["alc"], 2.87)
        self.assertAlmostEqual(vals["aec"], 0.51)
        self.assertAlmostEqual(vals["amc"], 0.59)

    # ── KFT ──

    def test_kft_values(self):
        vals = self._get_values(PAGE_KFT)
        self.assertAlmostEqual(vals["urea"], 33.44)
        self.assertAlmostEqual(vals["bun"], 15.63)
        self.assertAlmostEqual(vals["creatinine"], 0.76)
        self.assertAlmostEqual(vals["uric_acid"], 4.68)
        self.assertAlmostEqual(vals["egfr"], 123.29)

    # ── Thyroid ──

    def test_thyroid_values(self):
        vals = self._get_values(PAGE_THYROID)
        self.assertAlmostEqual(vals["total_t3"], 1.33)
        self.assertAlmostEqual(vals["total_t4"], 7.95)
        self.assertAlmostEqual(vals["tsh"], 3.52)

    # ── Vitamins ──

    def test_vitamin_b12(self):
        vals = self._get_values(PAGE_VITB12)
        self.assertIn("vitamin_b12", vals)
        self.assertAlmostEqual(vals["vitamin_b12"], 670)

    def test_vitamin_d(self):
        vals = self._get_values(PAGE_VITD)
        self.assertIn("vitamin_d", vals)
        self.assertAlmostEqual(vals["vitamin_d"], 18.6)

    # ── Iron / Calcium ──

    def test_iron(self):
        vals = self._get_values(PAGE_IRON)
        self.assertIn("serum_iron", vals)
        self.assertAlmostEqual(vals["serum_iron"], 87.81)

    def test_calcium(self):
        vals = self._get_values(PAGE_CALCIUM)
        self.assertIn("calcium", vals)
        self.assertAlmostEqual(vals["calcium"], 9.5)

    # ── Urine qualitative ──

    def test_urine_qualitative(self):
        qual = _extract_qualitative(PAGE_URINE, 1)
        self.assertIn("urine_protein", qual)
        self.assertIn("+", qual["urine_protein"].value)
        self.assertTrue(qual["urine_protein"].abnormal)

        self.assertIn("urine_glucose", qual)
        self.assertIn("+", qual["urine_glucose"].value)
        self.assertTrue(qual["urine_glucose"].abnormal)

        self.assertIn("urine_specific_gravity", qual)
        self.assertAlmostEqual(qual["urine_specific_gravity"].value, 1.030)

        self.assertIn("urine_ph", qual)
        self.assertAlmostEqual(qual["urine_ph"].value, 6.0)

    # ── Tumor Markers ──

    def test_tumor_markers(self):
        vals = self._get_values(PAGE_TUMOR)
        self.assertAlmostEqual(vals["afp"], 3.32)
        self.assertAlmostEqual(vals["cea"], 3.63)
        self.assertAlmostEqual(vals["ca19_9"], 10.7)
        self.assertAlmostEqual(vals["ca15_3"], 12.4)
        self.assertAlmostEqual(vals["psa"], 0.938)

    # ── Aggregate count ──

    def test_total_parsed_count(self):
        """All pages combined should yield 40+ values."""
        all_pages = [
            PAGE_HBAIC, PAGE_FASTING_GLUCOSE, PAGE_LFT, PAGE_LIPID,
            PAGE_CBC, PAGE_DIFF, PAGE_KFT, PAGE_THYROID,
            PAGE_VITB12, PAGE_VITD, PAGE_IRON, PAGE_CALCIUM,
            PAGE_TUMOR,
        ]
        total = 0
        for text in all_pages:
            found, _ = _extract_values_from_page(text, 1)
            total += len(found)
        # Plus qualitative
        qual = _extract_qualitative(PAGE_URINE, 1)
        total += len(qual)
        self.assertGreaterEqual(total, 40, f"Expected >=40 parsed values, got {total}")


if __name__ == "__main__":
    unittest.main()
