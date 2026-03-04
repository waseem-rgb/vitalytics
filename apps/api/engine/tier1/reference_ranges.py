"""Reference range loader and lookup."""

import json
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@lru_cache(maxsize=1)
def _load_ranges() -> dict:
    path = DATA_DIR / "reference_ranges.json"
    with open(path) as f:
        data = json.load(f)
    return {entry["test_id"]: entry for entry in data}


def get_all_ranges() -> dict:
    return _load_ranges()


def get_range(test_id: str) -> dict | None:
    return _load_ranges().get(test_id)


def get_reference_range(test_id: str, age: int, sex: str) -> dict | None:
    """Return {low, high, critical_low, critical_high, unit} for a test."""
    entry = get_range(test_id)
    if entry is None:
        return None

    sex_key = sex.lower() if sex.lower() in ("male", "female") else "male"

    if "universal" in entry:
        bounds = entry["universal"]
    elif sex_key in entry:
        bounds = entry[sex_key]
    else:
        bounds = entry.get("male", entry.get("universal", {}))

    return {
        "low": bounds.get("low"),
        "high": bounds.get("high"),
        "critical_low": entry.get("critical_low"),
        "critical_high": entry.get("critical_high"),
        "unit": entry.get("unit", ""),
    }


def get_panels() -> dict:
    """Return tests grouped by panel."""
    panels: dict[str, list] = {}
    panel_map = {
        # CBC
        "hemoglobin": "CBC", "hematocrit": "CBC", "mcv": "CBC", "mch": "CBC",
        "mchc": "CBC", "rdw": "CBC", "wbc": "CBC", "rbc": "CBC",
        "neutrophils": "CBC", "lymphocytes": "CBC", "platelets": "CBC",
        "reticulocyte_count": "CBC",
        "neutrophils_pct": "CBC", "lymphocytes_pct": "CBC", "monocytes_pct": "CBC",
        "eosinophils_pct": "CBC", "basophils_pct": "CBC", "aec": "CBC",
        # Iron
        "ferritin": "Iron Studies", "serum_iron": "Iron Studies", "tibc": "Iron Studies",
        "transferrin_saturation": "Iron Studies",
        # Vitamins
        "vitamin_b12": "Vitamins", "folate": "Vitamins", "vitamin_d": "Vitamins",
        # RFT / KFT
        "creatinine": "RFT", "bun": "RFT", "egfr": "RFT",
        "urine_albumin_cr_ratio": "RFT", "urea": "RFT", "uric_acid": "RFT",
        "bun_creat_ratio": "RFT",
        # Diabetes
        "fasting_glucose": "Diabetes", "hba1c": "Diabetes", "fasting_insulin": "Diabetes",
        "c_peptide": "Diabetes", "abg": "Diabetes",
        # Thyroid
        "tsh": "Thyroid", "free_t4": "Thyroid", "free_t3": "Thyroid",
        "total_t3": "Thyroid", "total_t4": "Thyroid",
        # LFT
        "alt": "LFT", "ast": "LFT", "alp": "LFT", "ggt": "LFT",
        "total_bilirubin": "LFT", "direct_bilirubin": "LFT",
        "indirect_bilirubin": "LFT", "albumin": "LFT",
        "total_protein": "LFT", "globulin": "LFT", "ag_ratio": "LFT",
        "ast_alt_ratio": "LFT",
        # Lipid
        "total_cholesterol": "Lipid", "ldl": "Lipid", "hdl": "Lipid",
        "triglycerides": "Lipid", "vldl": "Lipid", "chol_hdl_ratio": "Lipid",
        # Electrolytes
        "sodium": "Electrolytes", "potassium": "Electrolytes", "calcium": "Electrolytes",
        "magnesium": "Electrolytes", "phosphate": "Electrolytes", "chloride": "Electrolytes",
        "bicarbonate": "Electrolytes",
        # Inflammatory
        "esr": "Inflammatory", "crp": "Inflammatory", "hs_crp": "Inflammatory",
        # Urine
        "urine_protein": "Urine Analysis", "urine_glucose": "Urine Analysis",
        "urine_ketones": "Urine Analysis", "urine_specific_gravity": "Urine Analysis",
        "urine_ph": "Urine Analysis", "urine_pus_cells": "Urine Analysis",
        "urine_rbc": "Urine Analysis", "urine_casts": "Urine Analysis",
        "urine_bacteria": "Urine Analysis",
        # Tumor Markers
        "afp": "Tumor Markers", "cea": "Tumor Markers", "ca19_9": "Tumor Markers",
        "ca15_3": "Tumor Markers", "psa": "Tumor Markers", "ca125": "Tumor Markers",
        # Other
        "ldh": "Other",
    }
    ranges = _load_ranges()
    for test_id, entry in ranges.items():
        panel = panel_map.get(test_id, "Other")
        panels.setdefault(panel, []).append({
            "test_id": test_id,
            "name": entry.get("name", test_id),
            "unit": entry.get("unit", ""),
        })
    return panels
