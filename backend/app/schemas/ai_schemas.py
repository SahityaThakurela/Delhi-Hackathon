"""Pydantic schemas and shared Enums for Kyro AI, agents and real-time intelligence.

Defined strictly per Section 4 & 5 of docs/KYRO_TEAM_BIBLE.pdf.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =====================================================================
# Strict Enum Contracts (Identical in DB, Backend and Frontend)
# =====================================================================

class Dimension(str, Enum):
    compliance = "compliance"
    security_privacy = "security_privacy"
    clinical = "clinical"
    financial = "financial"
    integration = "integration"
    operations = "operations"


class AgentName(str, Enum):
    orchestrator = "orchestrator"
    compliance = "compliance"
    clinical_evidence = "clinical_evidence"
    security_privacy = "security_privacy"
    financial = "financial"
    integration_fit = "integration_fit"
    operations = "operations"
    skeptic = "skeptic"


class FindingStatus(str, Enum):
    supported = "supported"
    partially_supported = "partially_supported"
    contradictory = "contradictory"
    unverified = "unverified"
    insufficient_evidence = "insufficient_evidence"
    not_applicable = "not_applicable"


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ClaimOrigin(str, Enum):
    vendor_claim = "vendor_claim"
    independently_verified = "independently_verified"
    inferred = "inferred"


class InvStatus(str, Enum):
    draft = "draft"
    queued = "queued"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class CompatStatus(str, Enum):
    compatible = "compatible"
    partial = "partial"
    incompatible = "incompatible"
    unknown = "unknown"


class ReviewDecision(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    edited = "edited"


class DocStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class EvidenceSource(str, Enum):
    vendor_document = "vendor_document"
    government_portal = "government_portal"
    standard = "standard"
    research = "research"
    public_web = "public_web"
    hospital_data = "hospital_data"
    catalogue = "catalogue"


class DebateRole(str, Enum):
    claim = "claim"
    challenge = "challenge"
    rebuttal = "rebuttal"
    resolution = "resolution"


# =====================================================================
# P2 Contract Data Models (Section 5 Examples)
# =====================================================================

class EvidenceSummary(BaseModel):
    id: UUID
    relation: str = Field(..., description="'supports' | 'contradicts' | 'context'")
    source_type: EvidenceSource
    source_name: str
    page: Optional[int] = None
    excerpt: str
    source_date: Optional[date] = None
    is_independent: bool = False


class FindingResponse(BaseModel):
    id: UUID
    investigation_id: UUID
    agent: AgentName
    dimension: Dimension
    title: str
    description: str
    status: FindingStatus
    severity: Severity
    evidence_confidence: Confidence
    claim_origin: ClaimOrigin
    requirement_id: Optional[UUID] = None
    recommended_action: Optional[str] = None
    missing_evidence: Optional[str] = None
    review_decision: ReviewDecision = ReviewDecision.pending
    evidence: List[EvidenceSummary] = Field(default_factory=list)
    created_at: datetime


class DimensionScore(BaseModel):
    dimension: Dimension
    score: float
    weight: float
    confidence: float
    rationale: Optional[str] = None


class TrustScoreResponse(BaseModel):
    investigation_id: UUID
    overall_score: Optional[float] = None
    score_confidence: Optional[float] = None
    overall_risk: Optional[Severity] = None
    label: str = "Decision-support score. Not a certification."
    dimensions: List[DimensionScore] = Field(default_factory=list)
    top_risks: List[UUID] = Field(default_factory=list)
    missing_evidence_count: int = 0


class IntegrationCheckRow(BaseModel):
    id: UUID
    hospital_system: Dict[str, Any]
    requirement: str
    vendor_capability: str
    status: CompatStatus
    gap_description: Optional[str] = None
    effort: Optional[str] = None  # 'low' | 'medium' | 'high'
    recommendation: Optional[str] = None
    evidence_ids: List[UUID] = Field(default_factory=list)
    evidence_confidence: Confidence = Confidence.medium


class SocketEnvelope(BaseModel):
    event: str
    investigation_id: UUID
    seq: int
    ts: datetime
    data: Dict[str, Any]
