"""API v1 router package for Kyro backend."""

from fastapi import APIRouter

from backend.app.api.v1.evidence import router as evidence_router
from backend.app.api.v1.findings import router as findings_router
from backend.app.api.v1.integration import router as integration_router
from backend.app.api.v1.investigations import router as investigations_router
from backend.app.api.v1.trust import router as trust_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount P2-owned routers
api_v1_router.include_router(investigations_router)
api_v1_router.include_router(findings_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(trust_router)
api_v1_router.include_router(integration_router)

__all__ = ["api_v1_router"]
