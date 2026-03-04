"""Reference router — GET /reference/ranges, /reference/panels."""

from fastapi import APIRouter

from apps.api.engine.tier1.reference_ranges import get_all_ranges, get_panels

router = APIRouter(prefix="/api/v1/reference", tags=["reference"])


@router.get("/ranges")
async def get_ranges():
    """Return all reference ranges."""
    return get_all_ranges()


@router.get("/panels")
async def get_panel_groups():
    """Return test panel groupings."""
    return get_panels()
