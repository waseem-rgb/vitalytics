"""Tests for API endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "rag_ready" in data


@pytest.mark.asyncio
async def test_reference_ranges():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/reference/ranges")
    assert resp.status_code == 200
    data = resp.json()
    assert "hemoglobin" in data
    assert "sodium" in data


@pytest.mark.asyncio
async def test_reference_panels():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/reference/panels")
    assert resp.status_code == 200
    data = resp.json()
    assert "CBC" in data
    assert "Electrolytes" in data


@pytest.mark.asyncio
async def test_analyze_ida_case():
    """Integration test: POST /analyze with IDA demo case."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/analyze",
            json={
                "patient": {"age": 32, "sex": "female"},
                "lab_results": {
                    "hemoglobin": 9.8,
                    "mcv": 72,
                    "ferritin": 6,
                    "serum_iron": 35,
                    "tibc": 420,
                    "transferrin_saturation": 8,
                    "wbc": 6.5,
                    "platelets": 280000,
                },
            },
        )
    assert resp.status_code == 200
    data = resp.json()

    # Check structure
    assert "id" in data
    assert "timestamp" in data
    assert "patient" in data
    assert "tier1" in data
    assert "tier2" in data
    assert "tier3" in data

    # Tier 1
    assert "hemoglobin" in data["tier1"]
    assert data["tier1"]["hemoglobin"]["status"] == "low"

    # Tier 2
    pattern_ids = [p["id"] for p in data["tier2"]["patterns"]]
    assert "iron_deficiency_anemia" in pattern_ids

    # Tier 3
    assert "further_tests" in data["tier3"]
    assert "referrals" in data["tier3"]
    assert "lifestyle" in data["tier3"]


@pytest.mark.asyncio
async def test_analyze_with_previous_results():
    """Test trend analysis with previous results."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/analyze",
            json={
                "patient": {"age": 32, "sex": "female"},
                "lab_results": {"hemoglobin": 9.8, "mcv": 72, "ferritin": 6},
                "previous_results": {"hemoglobin": 10.5},
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    # Hemoglobin should have trend data
    hb = data["tier1"]["hemoglobin"]
    assert "trend" in hb
    assert hb["trend"]["direction"] == "down"


@pytest.mark.asyncio
async def test_get_analysis_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analysis/nonexistent-id")
    assert resp.status_code == 404
