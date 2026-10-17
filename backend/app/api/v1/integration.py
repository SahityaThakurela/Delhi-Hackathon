"""Integration compatibility and blueprint endpoints (P2 ownership).

Covers Section 6.7b of docs/KYRO_TEAM_BIBLE.pdf.
"""

from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter

from backend.app.services.integration_engine import (
    evaluate_integration_compatibility,
    generate_blueprint,
)

router = APIRouter(tags=["Integration Intelligence"])


@router.get("/investigations/{id}/integration")
async def get_integration_compatibility(id: UUID) -> Dict[str, Any]:
    """Retrieve integration compatibility matrix and summary for an investigation."""
    return evaluate_integration_compatibility(hospital_systems=[], vendor_product={})


@router.get("/investigations/{id}/integration/blueprint")
async def get_integration_blueprint(id: UUID) -> Dict[str, Any]:
    """Retrieve integration roadmap blueprint with phases, duration ranges, and risks."""
    return generate_blueprint(checks=[])
