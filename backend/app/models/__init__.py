"""SQLAlchemy Models package for Kyro.

Exports all domain models and native enums for metadata discovery and imports.
"""

from app.db.base import Base
from app.models.enums import (
    UserRole,
    SystemCategory,
    DeploymentModel,
    RiskAppetite,
    Dimension,
    AgentName,
    FindingStatus,
    Severity,
    Confidence,
    ClaimOrigin,
    InvStatus,
    RunStatus,
    ReviewDecision,
    CompatStatus,
    EvidenceSource,
    DocStatus,
    ReportStatus,
    AlertStatus,
    DebateRole,
    ALL_ENUMS,
)
from app.models.hospital import (
    Hospital,
    User,
    HospitalSystem,
    RequirementCatalogue,
    HospitalRequirement,
)
from app.models.vendor import (
    Vendor,
    Product,
)
from app.models.document import (
    Document,
    DocumentChunk,
)
from app.models.investigation import (
    Investigation,
    AgentRun,
    SteeringCommand,
    TimelineEvent,
)
from app.models.evidence import (
    Evidence,
    Finding,
    FindingEvidence,
    DebateMessage,
)
from app.models.scoring import (
    DimensionScore,
    IntegrationCheck,
    IntegrationBlueprint,
)
from app.models.reports import (
    Report,
    Review,
)
from app.models.monitoring import (
    MonitoringWatch,
    Alert,
)
from app.models.audit import (
    AuditLog,
)

__all__ = [
    "Base",
    # Enums
    "UserRole",
    "SystemCategory",
    "DeploymentModel",
    "RiskAppetite",
    "Dimension",
    "AgentName",
    "FindingStatus",
    "Severity",
    "Confidence",
    "ClaimOrigin",
    "InvStatus",
    "RunStatus",
    "ReviewDecision",
    "CompatStatus",
    "EvidenceSource",
    "DocStatus",
    "ReportStatus",
    "AlertStatus",
    "DebateRole",
    "ALL_ENUMS",
    # Models
    "Hospital",
    "User",
    "HospitalSystem",
    "RequirementCatalogue",
    "HospitalRequirement",
    "Vendor",
    "Product",
    "Document",
    "DocumentChunk",
    "Investigation",
    "AgentRun",
    "SteeringCommand",
    "TimelineEvent",
    "Evidence",
    "Finding",
    "FindingEvidence",
    "DebateMessage",
    "DimensionScore",
    "IntegrationCheck",
    "IntegrationBlueprint",
    "Report",
    "Review",
    "MonitoringWatch",
    "Alert",
    "AuditLog",
]
