"""Tier 2 — Disease staging (CKD KDIGO, HbA1c, Albuminuria)."""


def get_ckd_stage(egfr: float) -> dict:
    """KDIGO CKD staging based on eGFR."""
    if egfr >= 90:
        return {"stage": "G1", "label": "Normal Kidney Function", "color": "green",
                "description": "Normal kidney function. No CKD staging indicated based on eGFR alone.",
                "show": False}
    elif egfr >= 60:
        return {"stage": "G2", "label": "Mildly Decreased", "color": "yellow",
                "description": "Kidney damage with mildly decreased GFR",
                "show": True}
    elif egfr >= 45:
        return {"stage": "G3a", "label": "Mild-Moderate Decrease", "color": "orange",
                "description": "Mildly to moderately decreased GFR",
                "show": True}
    elif egfr >= 30:
        return {"stage": "G3b", "label": "Moderate-Severe Decrease", "color": "orange",
                "description": "Moderately to severely decreased GFR",
                "show": True}
    elif egfr >= 15:
        return {"stage": "G4", "label": "Severely Decreased", "color": "red",
                "description": "Severely decreased GFR",
                "show": True}
    else:
        return {"stage": "G5", "label": "Kidney Failure", "color": "darkred",
                "description": "Kidney failure — dialysis or transplant may be needed",
                "show": True}


def get_hba1c_stage(value: float) -> dict:
    """HbA1c staging for diabetes status."""
    if value < 5.7:
        return {"stage": "normal", "label": "Normal", "color": "green",
                "description": "Normal glycemic control"}
    elif value < 6.5:
        return {"stage": "prediabetes", "label": "Prediabetes", "color": "amber",
                "description": "Increased risk of diabetes — lifestyle intervention recommended"}
    elif value < 7.0:
        return {"stage": "diabetes_controlled", "label": "Diabetes (Controlled)", "color": "orange",
                "description": "Diabetes with reasonable glycemic control"}
    elif value < 8.0:
        return {"stage": "diabetes_suboptimal", "label": "Diabetes (Suboptimal)", "color": "red",
                "description": "Diabetes with suboptimal control — treatment intensification needed"}
    elif value < 9.0:
        return {"stage": "diabetes_poor", "label": "Diabetes (Poor Control)", "color": "red",
                "description": "Diabetes with poor control — significant complication risk"}
    else:
        return {"stage": "diabetes_very_poor", "label": "Diabetes (Very Poor)", "color": "darkred",
                "description": "Diabetes with very poor control — urgent intervention required"}


def get_albuminuria_stage(acr: float) -> dict:
    """KDIGO albuminuria staging based on urine albumin-to-creatinine ratio (mg/g)."""
    if acr < 30:
        return {"stage": "A1", "label": "Normal to Mildly Increased",
                "description": "Normal to mildly increased albuminuria"}
    elif acr < 300:
        return {"stage": "A2", "label": "Moderately Increased",
                "description": "Moderately increased albuminuria (microalbuminuria)"}
    else:
        return {"stage": "A3", "label": "Severely Increased",
                "description": "Severely increased albuminuria (macroalbuminuria)"}
