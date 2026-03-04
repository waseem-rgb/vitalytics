"""Indian lab report parser — handles digital PDFs from Predlabs, SRL, Thyrocare, Metropolis, Lal Path Labs.

Rewritten to use per-test regex patterns that match the ACTUAL raw text extracted by PyMuPDF.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

# ─────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────

@dataclass
class ParsedResult:
    value: float | str
    unit: str = ""
    ref_range: str = ""
    source_page: int = 0
    is_qualitative: bool = False
    abnormal: bool = False


@dataclass
class ParsedReport:
    patient: dict = field(default_factory=dict)
    results: dict[str, ParsedResult] = field(default_factory=dict)
    urine: dict[str, ParsedResult] = field(default_factory=dict)
    tumor_markers: dict[str, ParsedResult] = field(default_factory=dict)
    parse_confidence: float = 0.0
    total_tests_found: int = 0
    unmatched_tests: list[str] = field(default_factory=list)

    def get_flat_lab_results(self) -> dict[str, float]:
        """Return a flat dict of test_id -> numeric value for the analysis engine."""
        flat: dict[str, float] = {}
        for test_id, parsed in self.results.items():
            if isinstance(parsed.value, (int, float)):
                flat[test_id] = float(parsed.value)
        for test_id, parsed in self.urine.items():
            val = parsed.value
            if isinstance(val, str):
                plus_match = re.search(r"\+{1,4}", val)
                if plus_match:
                    flat[test_id] = float(len(plus_match.group(0)))
                elif val.lower() in ("positive", "present"):
                    flat[test_id] = 1.0
                elif val.lower() in ("negative", "absent", "nil", "none"):
                    flat[test_id] = 0.0
            elif isinstance(val, (int, float)):
                flat[test_id] = float(val)
        for test_id, parsed in self.tumor_markers.items():
            if isinstance(parsed.value, (int, float)):
                flat[test_id] = float(parsed.value)
        return flat


# ─────────────────────────────────────────────────────────────
# Regex-based test aliases: pattern -> standard_id
# Order matters — more specific patterns FIRST to avoid
# partial matches (e.g. "Absolute Eosinophil" before "Eosinophil")
# ─────────────────────────────────────────────────────────────

TEST_ALIASES: list[tuple[str, str]] = [
    # ── CBC ──
    (r"(?:Haemoglobin|Hemoglobin)\b", "hemoglobin"),
    (r"Total\s+WBC\s+Count", "wbc"),
    (r"Total\s+(?:Leucocyte|Leukocyte)\s+Count", "wbc"),
    (r"RBC\s+Count", "rbc"),
    (r"(?:Haematocrit|Hematocrit|Packed\s+Cell\s+Volume)\b", "hematocrit"),
    (r"\bMCV\b", "mcv"),
    (r"\bMCHC\b", "mchc"),
    (r"\bMCH\b(?!C)", "mch"),
    (r"RDW[-\s]CV", "rdw"),
    (r"RDW[-\s]SD", "rdw_sd"),
    (r"Platelet\s+Count", "platelets"),
    (r"Reticulocyte\s+Count", "reticulocyte_count"),

    # ── Differential (absolute MUST come before percentage) ──
    (r"Absolute\s+Eosinophil\s+Count", "aec"),
    (r"Absolute\s+Neutrophil\w*\s+Count", "anc"),
    (r"Absolute\s+Lymphocyte\s+Count", "alc"),
    (r"Absolute\s+Monocyte\s+Count", "amc"),
    (r"Absolute\s+Basophil\w*\s+Count", "abc"),
    (r"(?<!Absolute\s)Neutrophils?\b", "neutrophils_pct"),
    (r"(?<!Absolute\s)Lymphocytes?\b", "lymphocytes_pct"),
    (r"(?<!Absolute\s)Monocytes?\b", "monocytes_pct"),
    (r"(?<!Absolute\s)Eosinophil\b", "eosinophils_pct"),
    (r"(?<!Absolute\s)Basophils?\b", "basophils_pct"),

    # ── Diabetes ──
    (r"\bHbA1c\b", "hba1c"),
    (r"AVERAGE\s+BLOOD\s+GLUCOSE", "avg_blood_glucose"),
    (r"Glucose\s*Fasting|Fasting.*Glucose|FBS\b|Fasting\s+Blood\s+Sugar", "fasting_glucose"),
    (r"Glucose\s*(?:PP|Post\s*Prandial)|PP\s*(?:Blood\s*)?(?:Sugar|Glucose)", "pp_glucose"),
    (r"Fasting\s+Insulin", "fasting_insulin"),
    (r"C[-\s]?Peptide", "c_peptide"),

    # ── Lipid (specific before generic) ──
    (r"Non[\s\-]?HDL\s*Cholesterol", "non_hdl_cholesterol"),
    (r"Total\s+Cholesterol", "total_cholesterol"),
    (r"Triglycerides", "triglycerides"),
    (r"HDL\s+Cholesterol|HDL[-\s]C\b", "hdl"),
    (r"VLDL\s+Cholesterol", "vldl"),
    (r"(?<!Non[\s\-])LDL\s+Cholesterol|LDL[-\s]C\b", "ldl"),
    (r"CHOL\s*/\s*HDL\s+Ratio|TC\s*/\s*HDL", "chol_hdl_ratio"),
    (r"LDL\s*/\s*HDL\s+Ratio", "ldl_hdl_ratio"),
    (r"TG\s*/\s*HDL\s+Ratio", "tg_hdl_ratio"),

    # ── LFT ──
    (r"SGOT\s*/\s*SGPT\s+Ratio|AST\s*/\s*ALT\s+Ratio|De[-\s]?Ritis", "ast_alt_ratio"),
    (r"Bilirubin\s+Total", "total_bilirubin"),
    (r"Bilirubin\s+Direct", "direct_bilirubin"),
    (r"Bilirubin\s+Indirect", "indirect_bilirubin"),
    (r"SGOT\s*\(AST\)|(?<!\w)AST(?:\s*[-\s]?\s*serum)?\b", "ast"),
    (r"SGPT\s*\(ALT\)|(?<!\w)ALT(?:\s*[-\s]?\s*serum)?\b", "alt"),
    (r"Alkaline\s+Phosphatase", "alp"),
    (r"A\s*/\s*G\s+Ratio|Albumin\s*/\s*Globulin", "ag_ratio"),
    (r"Protein\s+Total|Total\s+Protein", "total_protein"),
    (r"(?<!Total\s)Albumin\b(?!\s*(?:Creat|Glob|/|to))", "albumin"),
    (r"(?<!\w)Globulin\b(?!\s*/)", "globulin"),
    (r"GGTP|Gamma[-\s]?GT|GGT\b", "ggt"),

    # ── KFT / RFT ──
    (r"BUN\s*/\s*Creatinine\s+Ratio", "bun_creat_ratio"),
    (r"Urea\s*/\s*Creatinine\s+Ratio", "urea_creat_ratio"),
    (r"Serum\s+Urea\b|(?<!\w)Urea\b(?!\s*/)", "urea"),
    (r"\bBUN\b(?!\s*/)", "bun"),
    (r"Serum\s+Creatinine|S\.\s*Creatinine", "creatinine"),
    (r"Serum\s+Uric\s*[Aa]cid|Uric\s+Acid", "uric_acid"),
    (r"\beGFR\b", "egfr"),
    (r"Urine\s+Albumin\s*(?:to\s*)?Creatinine\s+Ratio|Urine\s+ACR|Microalbumin\s+Creatinine", "urine_albumin_cr_ratio"),

    # ── Thyroid ──
    (r"THYROID\s+STIMULATING\s+HORMONE|(?<!\w)TSH\b", "tsh"),
    (r"TOTAL\s+TRIIODOTHYRONINE|Total\s+T3\b", "total_t3"),
    (r"TOTAL\s+THYROXINE|Total\s+T4\b", "total_t4"),
    (r"Free\s+T3\b|FT3\b", "free_t3"),
    (r"Free\s+T4\b|FT4\b", "free_t4"),
    (r"Anti[-\s]?TPO|Thyroid\s+Peroxidase\s+Antibod", "anti_tpo"),

    # ── Vitamins ──
    (r"Vitamin\s*B[-\s]?12\b", "vitamin_b12"),
    (r"Vitamin\s*D\s*(?:Total)?[-\s]*25[-\s]*Hydroxy|25[-\s]*(?:\(OH\)|OH)\s*(?:Vitamin\s*)?D", "vitamin_d"),
    (r"Folate\b|Folic\s+Acid", "folate"),

    # ── Iron ──
    (r"(?:Serum\s+)?(?:^|\b)IRON\b(?!\s*Binding)", "serum_iron"),
    (r"(?:Serum\s+)?Ferritin", "ferritin"),
    (r"TIBC|Total\s+Iron\s+Binding", "tibc"),
    (r"Transferrin\s+Saturation", "transferrin_saturation"),
    (r"UIBC\b", "uibc"),

    # ── Electrolytes / Minerals ──
    (r"CALCIUM\b(?:\s*[-\s]\s*(?:serum|total))?", "calcium"),
    (r"(?:Serum\s+)?Sodium\b|Na\+", "sodium"),
    (r"(?:Serum\s+)?Potassium\b|K\+", "potassium"),
    (r"(?:Serum\s+)?Chloride\b", "chloride"),
    (r"(?:Serum\s+)?Phosph(?:ate|orus)\b", "phosphate"),
    (r"(?:Serum\s+)?Magnesium\b", "magnesium"),
    (r"Bicarbonate\b", "bicarbonate"),

    # ── Inflammatory ──
    (r"\bESR\b|Erythrocyte\s+Sedimentation", "esr"),
    (r"\bhs[-\s]?CRP\b|High\s+Sensitivity\s+CRP", "hs_crp"),
    (r"\bCRP\b|C[-\s]?Reactive\s+Protein", "crp"),

    # ── Tumor Markers ──
    (r"ALPHA\s+FETO\s*PROTEIN|(?<!\w)AFP\b", "afp"),
    (r"\bCEA\b|Carcinoembryonic", "cea"),
    (r"CA\s*[-\s]?\s*19[\.\-]?\s*9", "ca19_9"),
    (r"CA\s*[-\s]?\s*15[\.\-]?\s*3", "ca15_3"),
    (r"CA\s*[-\s]?\s*125\b", "ca125"),
    (r"(?:TOTAL\s+)?PSA\b|Prostate[\s\-]Specific\s+Antigen", "psa"),

    # ── Other ──
    (r"\bLDH\b|Lactate\s+Dehydrogenase", "ldh"),
]

TUMOR_MARKER_IDS = {"afp", "cea", "ca19_9", "ca15_3", "ca125", "psa"}

# ─────────────────────────────────────────────────────────────
# Qualitative urine patterns
# ─────────────────────────────────────────────────────────────

URINE_QUALITATIVE: list[tuple[str, str, str]] = [
    # (regex, test_id, value_group_type)
    (r"Protein\s+Present\s*\((\++){1,4}\)", "urine_protein", "group1"),
    (r"Protein\s+Negative", "urine_protein", "literal_negative"),
    (r"Protein\s+Trace", "urine_protein", "literal_trace"),
    (r"Glucose\s+Present\s*\((\++){1,4}\)", "urine_glucose", "group1"),
    (r"Glucose\s+Negative", "urine_glucose", "literal_negative"),
    (r"Ketones?\s+Present\s*\((\++){1,4}\)", "urine_ketones", "group1"),
    (r"Ketones?\s+Negative", "urine_ketones", "literal_negative"),
    (r"Bile\s+Salt\s+Present", "urine_bile_salt", "literal_positive"),
    (r"Bile\s+Salt\s+Negative", "urine_bile_salt", "literal_negative"),
    (r"Bile\s+Pigment\s+Present", "urine_bile_pigment", "literal_positive"),
    (r"Bile\s+Pigment\s+Negative", "urine_bile_pigment", "literal_negative"),
]

URINE_NUMERIC: list[tuple[str, str]] = [
    (r"Specific\s+Gravity\s+([\d.]+)", "urine_specific_gravity"),
    (r"(?<!\w)pH\s+([\d.]+)", "urine_ph"),
]

# Lines to skip
SKIP_PATTERNS = re.compile(
    r"Patient\s*Name|Sample\s*ID|Reported\s*On|Registration\s*On|"
    r"Page\s+\d|END\s+OF|Note\s*:|Predlabs|PRED\s*LABS|"
    r"TEST\s+DONE|OBSERVED\s+VALUE|BIO\.?\s*REF|"
    r"Printed\s*On|Barcode|Report\s+ID|Ref\.?\s+By|"
    r"Disclaimer|Interpretation\s*:|^\*{3}",
    re.IGNORECASE,
)

# Section header patterns (don't try to extract values from these)
SECTION_HEADERS = re.compile(
    r"^(?:GLYCOSYLATED\s+HEMOGLOBIN|GLUCOSE\s*-\s*FASTING|"
    r"LIVER\s+FUNCTION|KIDNEY\s+BASIC|LIPID\s+PROFILE|"
    r"COMPLETE\s+BLOOD\s+COUNT|THYROID\s+PROFILE|"
    r"DIFFERENTIAL\s+COUNT|IRON\s+STUDY|"
    r"VITAMIN\s*-\s*(?:B|D)|"
    r"CUE\s*-\s*COMPLETE|TUMOU?R\s+MARKER|CANCER\s+MARKER|"
    r"HPLC\s+Method|Hexokinase|Chemical\s+Examination|"
    r"Physical\s+Examination|Microscopic|"
    r"CALCIUM\s*-\s*SERUM\s*$|"
    r"^\s*IRON\s*$|"
    r"^\s*\((?:ABG|Plasma)\)\s*$"
    r")",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────
# Patient info extraction
# ─────────────────────────────────────────────────────────────

def _extract_patient_info(full_text: str) -> dict:
    """Extract patient demographics from report header."""
    patient: dict = {}
    lines = full_text[:3000]

    # Name
    name_patterns = [
        r"[Pp]atient\s*[Nn]ame\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"[Nn]ame\s+of\s+[Pp]atient\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"[Nn]ame\s*[:\-]\s*(.+?)(?:\n|$)",
    ]
    for pat in name_patterns:
        m = re.search(pat, lines)
        if m:
            name = m.group(1).strip().strip(":")
            name = re.split(r"\s{3,}|\t|Age|Ref|Sample|Lab", name)[0].strip()
            if len(name) > 2:
                patient["name"] = name
                break

    # Age / Sex
    age_sex_patterns = [
        r"[Aa]ge\s*/\s*[Ss]ex\s*[:\-]?\s*(\d+)\s*(?:[Yy](?:ears?|rs?))?\s*/\s*([Mm]ale|[Ff]emale|[MmFf])\b",
        r"[Aa]ge\s*[:\-]?\s*(\d+)\s*(?:[Yy](?:ears?|rs?))?.*?[Ss]ex\s*[:\-]?\s*([Mm]ale|[Ff]emale|[MmFf])\b",
        r"(\d+)\s*(?:[Yy](?:ears?|rs?))\s*/\s*([Mm]ale|[Ff]emale|[MmFf])\b",
    ]
    for pat in age_sex_patterns:
        m = re.search(pat, lines)
        if m:
            patient["age"] = int(m.group(1))
            sex_raw = m.group(2).lower()
            patient["sex"] = "male" if sex_raw in ("male", "m") else "female"
            break

    # Report date
    date_patterns = [
        r"[Rr]eported\s*(?:[Oo]n)?\s*[:\-]?\s*(\d{1,2}\s+\w+,?\s+\d{4})",
        r"[Rr]eport\s*[Dd]ate\s*[:\-]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    ]
    for pat in date_patterns:
        m = re.search(pat, lines)
        if m:
            patient["report_date"] = m.group(1).strip()
            break

    return patient


# ─────────────────────────────────────────────────────────────
# Lab detection
# ─────────────────────────────────────────────────────────────

LAB_PATTERNS = {
    "predlabs": r"predlabs|pred\s*labs",
    "srl": r"srl\s*diagnostics|srl\s*ltd",
    "thyrocare": r"thyrocare",
    "metropolis": r"metropolis",
    "lal_path_labs": r"dr\.?\s*lal\s*path|lal\s*pathlabs",
    "apollo": r"apollo\s*diagnostics",
    "suburban": r"suburban\s*diagnostics",
    "healthians": r"healthians",
    "redcliffe": r"redcliffe",
}

def _detect_lab(full_text: str) -> str:
    text_lower = full_text.lower()
    for lab_name, pattern in LAB_PATTERNS.items():
        if re.search(pattern, text_lower):
            return lab_name
    return "unknown"


# ─────────────────────────────────────────────────────────────
# Core extraction: per-line regex matching
# ─────────────────────────────────────────────────────────────

# Numeric value pattern: captures first decimal number after test name
_NUM = re.compile(r"(\d+\.?\d*)")


def _extract_values_from_page(
    text: str, page_num: int, _context: list[str] | None = None,
) -> tuple[list[tuple[str, ParsedResult]], list[str]]:
    """Extract test-value pairs from a single page of text using regex."""
    found: list[tuple[str, ParsedResult]] = []
    unmatched: list[str] = []
    matched_lines: set[int] = set()

    lines = text.strip().split("\n")

    for i, line in enumerate(lines):
        raw_line = line
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Skip header/footer/section-header lines
        if SKIP_PATTERNS.search(line):
            continue
        if SECTION_HEADERS.match(line):
            continue

        # Try each test alias pattern
        for pattern, test_id in TEST_ALIASES:
            m = re.search(pattern, line, re.IGNORECASE)
            if not m:
                continue

            # Found test name — extract numeric value AFTER the match
            after_name = line[m.end():]

            # Strip parenthetical abbreviations like (T3), (AST), (Plasma)
            # but NOT (++) or (3+) which are qualitative values
            after_clean = re.sub(r"\([^)]*[a-zA-Z][^)]*\)", "", after_name)

            # Extract first number from remainder of line
            num_match = _NUM.search(after_clean)
            if num_match:
                try:
                    value = float(num_match.group(1))
                except ValueError:
                    continue

                # Extract unit (text right after the number)
                after_num = after_clean[num_match.end():].strip()
                unit = ""
                unit_match = re.match(
                    r"\s*(mg/d[lL]|g/d[lL]|gm/d[lL]|U/L|IU/m[lL]|ng/m[lL]|"
                    r"pg/m[lL]|µg/d[lL]|µIU/m[lL]|fL|pg|%|"
                    r"10\^3\s*/\s*uL|10\^6\s*/\s*uL|mm/hr|"
                    r"mEq/L|mmol/L|cells/µL|cells/cumm)",
                    after_num, re.IGNORECASE,
                )
                if unit_match:
                    unit = unit_match.group(1)

                # Extract reference range (everything after unit, simplified)
                ref_range = ""
                rest = after_num[unit_match.end():].strip() if unit_match else after_num.strip()
                # Clean out method names
                rest = re.sub(
                    r"(?:Cyanide\s+Free|Elec\.\s*Impedance|Diazo|IFCC|"
                    r"AMP\s+optimised|Biuret|Bromo|Calculated|"
                    r"Hexokinase|HPLC|Turbidimetric|Colorimetric|"
                    r"Enzymatic|Reference\s+Method|with\s+P5P|"
                    r"Photometric|Kinetic|Ion\s+Selective|"
                    r"Immunoturbidimetry|Chemiluminescence|CLIA|ECLIA).*$",
                    "", rest, flags=re.IGNORECASE,
                ).strip()
                if rest:
                    ref_range = rest

                parsed = ParsedResult(
                    value=value,
                    unit=unit,
                    ref_range=ref_range,
                    source_page=page_num,
                )
                found.append((test_id, parsed))
                matched_lines.add(i)
                break  # Only match first alias per line

            else:
                # No number on this line — check NEXT 1-3 lines (multi-line format)
                # e.g. "Glucose Fasting\n(Plasma)\n244.77 mg/dl"
                lookahead = min(i + 4, len(lines))
                for j in range(i + 1, lookahead):
                    next_line = lines[j].strip()
                    if not next_line or SKIP_PATTERNS.search(next_line):
                        continue
                    if SECTION_HEADERS.match(next_line):
                        continue
                    # Skip parenthetical-only lines like "(ABG)", "(Plasma)"
                    if re.match(r"^\(.*\)$", next_line):
                        continue
                    num_match = _NUM.search(next_line)
                    if num_match:
                        try:
                            value = float(num_match.group(1))
                        except ValueError:
                            continue
                        # Extract unit from the same line
                        after_num = next_line[num_match.end():].strip()
                        unit = ""
                        unit_m = re.match(
                            r"\s*(mg/d[lL]|g/d[lL]|gm/d[lL]|U/L|IU/m[lL]|ng/m[lL]|"
                            r"pg/m[lL]|µg/d[lL]|µIU/m[lL]|fL|pg|%|"
                            r"10\^3\s*/\s*uL|10\^6\s*/\s*uL|mm/hr|"
                            r"mEq/L|mmol/L)",
                            after_num, re.IGNORECASE,
                        )
                        if unit_m:
                            unit = unit_m.group(1)
                        parsed = ParsedResult(
                            value=value,
                            unit=unit,
                            ref_range="",
                            source_page=page_num,
                        )
                        found.append((test_id, parsed))
                        matched_lines.add(i)
                        matched_lines.add(j)
                        break
                break  # Move to next line after trying multi-line

    return found, unmatched


def _extract_qualitative(text: str, page_num: int) -> dict[str, ParsedResult]:
    """Extract qualitative urine values from text."""
    results: dict[str, ParsedResult] = {}

    for pattern, test_id, val_type in URINE_QUALITATIVE:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            if val_type == "group1":
                value = m.group(1)
            elif val_type == "literal_negative":
                value = "negative"
            elif val_type == "literal_trace":
                value = "trace"
            elif val_type == "literal_positive":
                value = "positive"
            else:
                value = "unknown"

            # Determine abnormality
            abnormal = value not in ("negative", "trace")

            results[test_id] = ParsedResult(
                value=value,
                ref_range="negative",
                source_page=page_num,
                is_qualitative=True,
                abnormal=abnormal,
            )

    for pattern, test_id in URINE_NUMERIC:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1))
                results[test_id] = ParsedResult(
                    value=val,
                    source_page=page_num,
                )
            except ValueError:
                pass

    return results


# ─────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────

def parse_indian_lab_pdf(pdf_content: bytes) -> ParsedReport:
    """Parse an Indian lab report PDF and extract all values.

    Args:
        pdf_content: Raw bytes of the PDF file.

    Returns:
        ParsedReport with patient info, results, urine, and tumor markers.
    """
    if not HAS_FITZ:
        raise RuntimeError("PyMuPDF (fitz) is required. Install with: pip install PyMuPDF")

    doc = fitz.open(stream=pdf_content, filetype="pdf")
    report = ParsedReport()

    all_text = ""
    page_texts: list[tuple[int, str]] = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        page_texts.append((i + 1, text))
        all_text += text + "\n"
    doc.close()

    # Detect lab and extract patient info
    report.patient = _extract_patient_info(all_text)
    report.patient["lab"] = _detect_lab(all_text)

    # Extract values from each page
    for page_num, text in page_texts:
        # Quantitative values
        found, unmatched = _extract_values_from_page(text, page_num)
        report.unmatched_tests.extend(unmatched)

        for test_id, parsed in found:
            if test_id.startswith("urine_"):
                if test_id not in report.urine:
                    report.urine[test_id] = parsed
            elif test_id in TUMOR_MARKER_IDS:
                if test_id not in report.tumor_markers:
                    report.tumor_markers[test_id] = parsed
            else:
                if test_id not in report.results:
                    report.results[test_id] = parsed

        # Qualitative urine values
        qual = _extract_qualitative(text, page_num)
        for test_id, parsed in qual.items():
            if test_id not in report.urine:
                report.urine[test_id] = parsed

    # Deduplicate unmatched
    seen: set[str] = set()
    unique: list[str] = []
    for name in report.unmatched_tests:
        low = name.lower()
        if low not in seen:
            seen.add(low)
            unique.append(name)
    report.unmatched_tests = unique

    # Totals and confidence
    report.total_tests_found = (
        len(report.results) + len(report.urine) + len(report.tumor_markers)
    )

    if report.total_tests_found >= 30:
        report.parse_confidence = 0.95
    elif report.total_tests_found >= 20:
        report.parse_confidence = 0.90
    elif report.total_tests_found >= 10:
        report.parse_confidence = 0.80
    elif report.total_tests_found >= 5:
        report.parse_confidence = 0.60
    else:
        report.parse_confidence = 0.30

    # Indian lab corrections
    _apply_indian_lab_corrections(report)

    return report


def _apply_indian_lab_corrections(report: ParsedReport):
    """Apply corrections for common Indian lab reporting conventions."""
    # WBC: Indian labs report as X.XX (thousands), engine expects thousands
    wbc = report.results.get("wbc")
    if wbc and isinstance(wbc.value, (int, float)):
        if wbc.value < 100:
            wbc.value = round(wbc.value * 1000, 0)

    # Platelets: Indian labs report as XXX (thousands), engine expects raw count
    plt = report.results.get("platelets")
    if plt and isinstance(plt.value, (int, float)):
        if plt.value < 1000:
            plt.value = round(plt.value * 1000, 0)

    # AEC: may be reported in thousands (e.g., 0.51 = 510)
    aec = report.results.get("aec")
    if aec and isinstance(aec.value, (int, float)):
        if aec.value < 10:
            aec.value = round(aec.value * 1000, 0)

    # ANC, ALC, AMC: same thousands convention
    for abs_id in ("anc", "alc", "amc", "abc"):
        ab = report.results.get(abs_id)
        if ab and isinstance(ab.value, (int, float)):
            if ab.value < 10:
                ab.value = round(ab.value * 1000, 0)
