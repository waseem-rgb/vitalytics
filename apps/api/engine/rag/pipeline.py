"""RAG — Full analysis orchestrator: Tier 1 → Tier 2 → Tier 3 → RAG."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone

from apps.api.engine.tier1.interpreter import interpret_panel
from apps.api.engine.tier1.trend import compare_trend
from apps.api.engine.tier2.pattern_engine import evaluate_rules
from apps.api.engine.tier2.staging import get_ckd_stage, get_hba1c_stage, get_albuminuria_stage
from apps.api.engine.tier3.further_tests import get_further_tests
from apps.api.engine.tier3.referrals import get_referral
from apps.api.engine.tier3.lifestyle import get_lifestyle_plan

logger = logging.getLogger(__name__)


def run_full_analysis(
    lab_results: dict,
    age: int,
    sex: str,
    previous_results: dict | None = None,
    use_rag: bool = False,
) -> dict:
    """Run the full 3-tier analysis pipeline.

    Returns a complete analysis dict with tier1, tier2, tier3, and optional rag_narrative.
    """
    analysis_id = str(uuid.uuid4())

    # ── Tier 1: Interpretation ──
    tier1 = interpret_panel(lab_results, age, sex)

    # Add trend data if previous results provided
    if previous_results:
        for test_id, interp in tier1.items():
            if test_id in previous_results:
                try:
                    prev_val = float(previous_results[test_id])
                    curr_val = float(interp["value"])
                    trend = compare_trend(test_id, curr_val, prev_val, days_between=90, age=age, sex=sex)
                    interp["trend"] = trend
                    interp["previous_value"] = prev_val
                except (TypeError, ValueError):
                    pass

    # ── Tier 2: Clinical Patterns ──
    patterns = evaluate_rules(lab_results, age, sex)

    # Staging
    staging = {}
    if "egfr" in lab_results:
        try:
            staging["ckd"] = get_ckd_stage(float(lab_results["egfr"]))
        except (TypeError, ValueError):
            pass
    if "hba1c" in lab_results:
        try:
            staging["hba1c"] = get_hba1c_stage(float(lab_results["hba1c"]))
        except (TypeError, ValueError):
            pass
    if "urine_albumin_cr_ratio" in lab_results:
        try:
            staging["albuminuria"] = get_albuminuria_stage(float(lab_results["urine_albumin_cr_ratio"]))
        except (TypeError, ValueError):
            pass

    tier2 = {
        "patterns": patterns,
        "staging": staging,
    }

    # ── Tier 3: Action Plans ──
    existing_tests = set(lab_results.keys())
    pattern_ids = [p["id"] for p in patterns]

    further_tests = []
    referrals = []

    for p in patterns:
        tests = get_further_tests(p["id"], existing_tests)
        if tests:
            further_tests.append({
                "pattern_id": p["id"],
                "tests": tests,
            })

        ref = get_referral(p["id"], p.get("severity", "moderate"))
        if ref:
            referrals.append({
                "pattern_id": p["id"],
                **ref,
            })

    lifestyle = get_lifestyle_plan(pattern_ids, age, sex) if pattern_ids else {}

    tier3 = {
        "further_tests": further_tests,
        "referrals": referrals,
        "lifestyle": lifestyle,
    }

    # ── RAG Narrative (auto-detect availability) ──
    # The use_rag parameter is kept for backward compatibility but ignored.
    # RAG runs automatically when patterns exist, the vector store is ready,
    # and the ANTHROPIC_API_KEY environment variable is set.
    rag_narrative = None
    if patterns:
        try:
            from apps.api.engine.rag.vector_store import is_ready
            rag_available = is_ready() and bool(os.environ.get("ANTHROPIC_API_KEY"))
            if rag_available:
                from apps.api.engine.rag.retriever import build_clinical_query, retrieve_context
                from apps.api.engine.rag.generator import generate_narrative

                query = build_clinical_query(patterns, lab_results)
                # Determine primary clinical domain
                domains = [p.get("category", "").lower() for p in patterns]
                primary_domain = domains[0] if domains else None
                domain_map = {
                    "cbc": "hematology",
                    "rft": "nephrology",
                    "diabetes": "endocrinology",
                    "thyroid": "endocrinology",
                    "lft": "hepatology",
                    "lipid": "cardiology",
                    "electrolyte": "nephrology",
                }
                clinical_domain = domain_map.get(primary_domain)

                chunks = retrieve_context(query, clinical_domain=clinical_domain, top_k=5)
                if chunks:
                    patient_context = {"age": age, "sex": sex}
                    rag_narrative = generate_narrative(patient_context, chunks, patterns)
        except Exception:
            # Silently skip RAG on any error — no warnings to the user
            pass

    result = {
        "id": analysis_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "patient": {"age": age, "sex": sex},
        "tier1": tier1,
        "tier2": tier2,
        "tier3": tier3,
    }

    if rag_narrative:
        result["rag_narrative"] = rag_narrative

    return result
