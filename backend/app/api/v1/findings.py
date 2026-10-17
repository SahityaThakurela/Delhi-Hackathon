"""Findings endpoints (P2 ownership).

Covers findings queries per Section 6.7 of docs/KYRO_TEAM_BIBLE.pdf.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter

from backend.app.schemas.ai_schemas import (
    AgentName,
    Dimension,
    FindingStatus,
    ReviewDecision,
    Severity,
)

router = APIRouter(tags=["Findings"])


@router.get("/investigations/{id}/findings")
async def list_investigation_findings(
    id: UUID,
    dimension: Optional[Dimension] = None,
    status: Optional[FindingStatus] = None,
    severity: Optional[Severity] = None,
    review_decision: Optional[ReviewDecision] = None,
    agent: Optional[AgentName] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Paginated findings for an investigation with evidence summaries."""
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/findings/{id}")
async def get_finding_detail(id: UUID) -> Dict[str, Any]:
    """Full finding details including evidence rows, debate history, and reviews."""
    return {
        "id": str(id),
        "title": "Finding Detail Placeholder",
        "description": "Details will be populated from DB.",
        "status": "unverified",
        "severity": "medium",
        "evidence_confidence": "medium",
        "claim_origin": "vendor_claim",
        "evidence": [],
        "review_decision": "pending",
    }
