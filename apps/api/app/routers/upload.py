"""Upload router — Parse lab report PDFs/images using Indian lab parser."""

from fastapi import APIRouter, UploadFile, File, HTTPException

from apps.api.engine.ocr.indian_lab_parser import parse_indian_lab_pdf, HAS_FITZ

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])


@router.post("/parse")
async def parse_upload(file: UploadFile = File(...)):
    """Parse an uploaded lab report (PDF or image) and extract values.

    Uses the Indian lab parser for structured digital PDFs (Predlabs, SRL, etc.).
    Falls back to basic OCR for scanned images.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    content = await file.read()

    if ext == "pdf":
        if not HAS_FITZ:
            raise HTTPException(status_code=501, detail="PyMuPDF not installed for PDF parsing")
        try:
            report = parse_indian_lab_pdf(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")

        return {
            "patient": report.patient,
            "parsed_results": report.get_flat_lab_results(),
            "results_detail": {
                k: {"value": v.value, "unit": v.unit, "ref_range": v.ref_range, "source_page": v.source_page}
                for k, v in report.results.items()
            },
            "urine": {
                k: {"value": v.value, "ref_range": v.ref_range, "abnormal": v.abnormal}
                for k, v in report.urine.items()
            },
            "tumor_markers": {
                k: {"value": v.value, "unit": v.unit, "ref_range": v.ref_range}
                for k, v in report.tumor_markers.items()
            },
            "confidence": report.parse_confidence,
            "total_tests_found": report.total_tests_found,
            "unmatched": report.unmatched_tests,
        }

    elif ext in ("png", "jpg", "jpeg", "tiff", "bmp"):
        try:
            import pytesseract
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(image)
        except ImportError:
            raise HTTPException(
                status_code=501,
                detail="pytesseract/Pillow not installed for image OCR"
            )

        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from image")

        # For images, use basic extraction
        from apps.api.engine.ocr.indian_lab_parser import (
            _extract_patient_info,
            _extract_values_from_page,
        )
        patient = _extract_patient_info(text)
        found, unmatched = _extract_values_from_page(text, 1, [])
        results = {}
        for test_id, parsed in found:
            if isinstance(parsed.value, (int, float)):
                results[test_id] = parsed.value

        return {
            "patient": patient,
            "parsed_results": results,
            "confidence": min(1.0, len(results) / 10),
            "total_tests_found": len(results),
            "unmatched": unmatched,
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Use PDF, PNG, JPG.")
