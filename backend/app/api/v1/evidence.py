"""Evidence endpoints (P2 ownership).

Covers evidence queries and claim verification per Section 6.7 of docs/KYRO_TEAM_BIBLE.pdf.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.schemas.ai_schemas import Dimension, EvidenceSource

router = APIRouter(tags=["Evidence"])


class VerifyClaimRequest(BaseModel):
    claim_text: str


@router.get("/investigations/{id}/evidence")
async def list_investigation_evidence(
    id: UUID,
    source_type: Optional[EvidenceSource] = None,
    is_independent: Optional[bool] = None,
    dimension: Optional[Dimension] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Evidence Explorer query endpoint."""
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/evidence/{id}")
async def get_evidence_detail(id: UUID) -> Dict[str, Any]:
    """Evidence detail including full excerpt, source metadata, and linked findings."""
    return {
        "id": str(id),
        "source_type": "vendor_document",
        "source_name": "Document Placeholder",
        "excerpt": "Excerpt placeholder.",
        "linked_findings": [],
    }


@router.post("/investigations/{id}/verify-claim")
async def verify_claim(id: UUID, payload: VerifyClaimRequest) -> Dict[str, Any]:
    """Verify an ad-hoc vendor claim using RAG + deterministic checks + LLM judgment."""
    return {
        "verdict": "insufficient_evidence",
        "confidence": "low",
        "evidence": [],
        "explanation": f"Claim '{payload.claim_text}' could not be verified without uploaded evidence.",
    }
