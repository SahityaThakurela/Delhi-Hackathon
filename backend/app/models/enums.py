"""
All PostgreSQL ENUM types for KYRO.

Defined once here and imported by every model file.
Names and values match the bible DDL exactly – do not rename.
"""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    procurement = "procurement"
    it = "it"
    security = "security"
    clinical = "clinical"
    reviewer = "reviewer"


class SystemCategory(str, enum.Enum):
    his_emr = "his_emr"
    lis = "lis"
    pacs = "pacs"
    ris = "ris"
    erp = "erp"
    billing = "billing"
    abdm_gateway = "abdm_gateway"
    other = "other"


class DeploymentModel(str, enum.Enum):
    on_prem = "on_prem"
    private_cloud = "private_cloud"
    public_cloud = "public_cloud"
    hybrid = "hybrid"
    saas = "saas"


class RiskAppetite(str, enum.Enum):
    conservative = "conservative"
    balanced = "balanced"
    aggressive = "aggressive"


class Dimension(str, enum.Enum):
    compliance = "compliance"
    security_privacy = "security_privacy"
    clinical = "clinical"
    financial = "financial"
    integration = "integration"
    operations = "operations"


class AgentName(str, enum.Enum):
    orchestrator = "orchestrator"
    compliance = "compliance"
    clinical_evidence = "clinical_evidence"
    security_privacy = "security_privacy"
    financial = "financial"
    integration_fit = "integration_fit"
    operations = "operations"
    skeptic = "skeptic"


class FindingStatus(str, enum.Enum):
    supported = "supported"
    partially_supported = "partially_supported"
    contradictory = "contradictory"
    unverified = "unverified"
    insufficient_evidence = "insufficient_evidence"
    not_applicable = "not_applicable"


class Severity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Confidence(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class ClaimOrigin(str, enum.Enum):
    vendor_claim = "vendor_claim"
    independently_verified = "independently_verified"
    inferred = "inferred"


class InvStatus(str, enum.Enum):
    draft = "draft"
    queued = "queued"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class ReviewDecision(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    edited = "edited"


class CompatStatus(str, enum.Enum):
    compatible = "compatible"
    partial = "partial"
    incompatible = "incompatible"
    unknown = "unknown"


class EvidenceSource(str, enum.Enum):
    vendor_document = "vendor_document"
    government_portal = "government_portal"
    standard = "standard"
    research = "research"
    public_web = "public_web"
    hospital_data = "hospital_data"
    catalogue = "catalogue"


class DocStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class ReportStatus(str, enum.Enum):
    draft = "draft"
    in_review = "in_review"
    final = "final"


class AlertStatus(str, enum.Enum):
    new = "new"
    acknowledged = "acknowledged"
    dismissed = "dismissed"


class DebateRole(str, enum.Enum):
    claim = "claim"
    challenge = "challenge"
    rebuttal = "rebuttal"
    resolution = "resolution"
