import enum
from sqlalchemy.dialects.postgresql import ENUM


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


# PostgreSQL Native ENUM instances with exact Bible names
user_role_enum = ENUM(UserRole, name="user_role", create_type=False)
system_category_enum = ENUM(SystemCategory, name="system_category", create_type=False)
deployment_model_enum = ENUM(DeploymentModel, name="deployment_model", create_type=False)
risk_appetite_enum = ENUM(RiskAppetite, name="risk_appetite", create_type=False)
dimension_enum = ENUM(Dimension, name="dimension", create_type=False)
agent_name_enum = ENUM(AgentName, name="agent_name", create_type=False)
finding_status_enum = ENUM(FindingStatus, name="finding_status", create_type=False)
severity_enum = ENUM(Severity, name="severity", create_type=False)
confidence_enum = ENUM(Confidence, name="confidence", create_type=False)
claim_origin_enum = ENUM(ClaimOrigin, name="claim_origin", create_type=False)
inv_status_enum = ENUM(InvStatus, name="inv_status", create_type=False)
run_status_enum = ENUM(RunStatus, name="run_status", create_type=False)
review_decision_enum = ENUM(ReviewDecision, name="review_decision", create_type=False)
compat_status_enum = ENUM(CompatStatus, name="compat_status", create_type=False)
evidence_source_enum = ENUM(EvidenceSource, name="evidence_source", create_type=False)
doc_status_enum = ENUM(DocStatus, name="doc_status", create_type=False)
report_status_enum = ENUM(ReportStatus, name="report_status", create_type=False)
alert_status_enum = ENUM(AlertStatus, name="alert_status", create_type=False)
debate_role_enum = ENUM(DebateRole, name="debate_role", create_type=False)

ALL_ENUMS = [
    ("user_role", UserRole),
    ("system_category", SystemCategory),
    ("deployment_model", DeploymentModel),
    ("risk_appetite", RiskAppetite),
    ("dimension", Dimension),
    ("agent_name", AgentName),
    ("finding_status", FindingStatus),
    ("severity", Severity),
    ("confidence", Confidence),
    ("claim_origin", ClaimOrigin),
    ("inv_status", InvStatus),
    ("run_status", RunStatus),
    ("review_decision", ReviewDecision),
    ("compat_status", CompatStatus),
    ("evidence_source", EvidenceSource),
    ("doc_status", DocStatus),
    ("report_status", ReportStatus),
    ("alert_status", AlertStatus),
    ("debate_role", DebateRole),
]
