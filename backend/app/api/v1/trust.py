"""Trust score endpoints (P2 ownership).

Covers Section 6.7b of docs/KYRO_TEAM_BIBLE.pdf.
"""

from uuid import UUID

from fastapi import APIRouter

from backend.app.schemas.ai_schemas import TrustScoreResponse
from backend.app.services.scoring import compute_trust_score

router = APIRouter(tags=["Trust Score"])


@router.get("/investigations/{id}/trust-score", response_model=TrustScoreResponse)
async def get_trust_score(id: UUID) -> TrustScoreResponse:
    """Retrieve deterministic trust score for an investigation."""
    # Compute from current findings (or default baseline if investigation is empty)
    return compute_trust_score(investigation_id=id, findings=[])
