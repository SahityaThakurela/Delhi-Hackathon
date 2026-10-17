"""Investigations endpoints (P2 ownership).

Covers Section 6.6 of docs/KYRO_TEAM_BIBLE.pdf.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from backend.app.schemas.ai_schemas import Dimension, InvStatus

router = APIRouter(prefix="/investigations", tags=["Investigations"])


class CreateInvestigationRequest(BaseModel):
    vendor_id: UUID
    product_id: Optional[UUID] = None
    title: Optional[str] = None
    dimensions: List[Dimension] = Field(
        default_factory=lambda: [
            Dimension.compliance,
            Dimension.security_privacy,
            Dimension.integration,
            Dimension.clinical,
            Dimension.financial,
            Dimension.operations,
        ]
    )
    instructions: Optional[str] = None


class SteerRequest(BaseModel):
    instruction: str


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_investigation(payload: CreateInvestigationRequest) -> Dict[str, Any]:
    """Create a draft investigation per Section 6.6."""
    return {
        "status": "draft",
        "vendor_id": str(payload.vendor_id),
        "dimensions": [d.value for d in payload.dimensions],
        "message": "Draft investigation created.",
    }


@router.get("")
async def list_investigations(
    vendor_id: Optional[UUID] = None,
    status: Optional[InvStatus] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Paginated list of investigations."""
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/{id}")
async def get_investigation_detail(id: UUID) -> Dict[str, Any]:
    """Investigation detail with agents[] and counts{} matching Section 5 shape."""
    return {
        "id": str(id),
        "title": "Investigation Detail",
        "status": "draft",
        "dimensions": [d.value for d in Dimension],
        "agents": [],
        "overall_score": None,
        "score_confidence": None,
        "overall_risk": None,
        "counts": {"findings": 0, "critical": 0, "high": 0, "evidence": 0},
    }


@router.post("/{id}/start", status_code=status.HTTP_202_ACCEPTED)
async def start_investigation(id: UUID) -> Dict[str, Any]:
    """Queue LangGraph investigation run."""
    return {"status": "queued", "investigation_id": str(id)}


@router.post("/{id}/pause")
async def pause_investigation(id: UUID) -> Dict[str, Any]:
    """Pause investigation between agent steps."""
    return {"status": "paused", "investigation_id": str(id)}


@router.post("/{id}/resume")
async def resume_investigation(id: UUID) -> Dict[str, Any]:
    """Resume paused investigation."""
    return {"status": "running", "investigation_id": str(id)}


@router.post("/{id}/cancel")
async def cancel_investigation(id: UUID) -> Dict[str, Any]:
    """Cancel investigation."""
    return {"status": "cancelled", "investigation_id": str(id)}


@router.get("/{id}/agents")
async def get_agent_runs(id: UUID) -> List[Dict[str, Any]]:
    """List agent_runs with status, progress, and current_task."""
    return []


@router.get("/{id}/timeline")
async def get_timeline(id: UUID, after_seq: Optional[int] = None) -> List[Dict[str, Any]]:
    """Ordered timeline_events for replay."""
    return []


@router.get("/{id}/debate")
async def get_debate(id: UUID, finding_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
    """Ordered debate messages, optionally filtered by finding_id."""
    return []


@router.post("/{id}/steer")
async def steer_investigation(id: UUID, payload: SteerRequest) -> Dict[str, Any]:
    """Live steering command for running orchestrator."""
    return {
        "id": str(id),
        "instruction": payload.instruction,
        "parsed": {"prioritise": []},
        "status": "acknowledged",
    }


@router.get("/{id}/gaps")
async def get_investigation_gaps(id: UUID) -> List[Dict[str, Any]]:
    """Missing evidence list: requirement, why_needed, suggested_document_type."""
    return []
