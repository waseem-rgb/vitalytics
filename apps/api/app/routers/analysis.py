"""Analysis router — POST /analyze, GET /analysis/{id}."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from apps.api.app.models.schemas import AnalysisRequest, AnalysisResponse
from apps.api.app.core.database import save_analysis, get_analysis, list_analyses
from apps.api.engine.rag.pipeline import run_full_analysis
from apps.api.engine.tier3.report_gen import generate_pdf_report, HAS_REPORTLAB

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analyze", response_model=None)
async def analyze(request: AnalysisRequest):
    """Run full 3-tier lab analysis."""
    result = run_full_analysis(
        lab_results=request.lab_results,
        age=request.patient.age,
        sex=request.patient.sex,
        previous_results=request.previous_results,
        use_rag=True,  # Always True — pipeline auto-detects RAG availability
    )

    # Persist
    save_analysis(result)

    return result


@router.get("/analysis/{analysis_id}")
async def get_analysis_by_id(analysis_id: str):
    """Retrieve a previously saved analysis."""
    result = get_analysis(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/analyses")
async def list_all_analyses(limit: int = 20):
    """List recent analyses."""
    return list_analyses(limit=limit)


@router.get("/reports/{analysis_id}/pdf")
async def download_pdf_report(analysis_id: str):
    """Download PDF report for an analysis."""
    if not HAS_REPORTLAB:
        raise HTTPException(status_code=501, detail="reportlab not installed — PDF generation unavailable")

    result = get_analysis(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    pdf_bytes = generate_pdf_report(result)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=vitalytics_report_{analysis_id[:8]}.pdf"},
    )
