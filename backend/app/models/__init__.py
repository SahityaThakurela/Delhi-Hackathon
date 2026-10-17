"""Import all models so Alembic's autogenerate sees them."""
from app.models.hospital import Hospital, User, HospitalSystem
from app.models.requirements import RequirementCatalogue, HospitalRequirement
from app.models.vendor import Vendor, Product
from app.models.document import Document, DocumentChunk
from app.models.investigation import Investigation, AgentRun, TimelineEvent, SteeringCommand
from app.models.evidence import Evidence, Finding, FindingEvidence, DebateMessage
from app.models.scoring import DimensionScore, IntegrationCheck, IntegrationBlueprint
from app.models.reports import Report, Review
from app.models.monitoring import MonitoringWatch, Alert
from app.models.audit import AuditLog

__all__ = [
    "Hospital", "User", "HospitalSystem",
    "RequirementCatalogue", "HospitalRequirement",
    "Vendor", "Product",
    "Document", "DocumentChunk",
    "Investigation", "AgentRun", "TimelineEvent", "SteeringCommand",
    "Evidence", "Finding", "FindingEvidence", "DebateMessage",
    "DimensionScore", "IntegrationCheck", "IntegrationBlueprint",
    "Report", "Review",
    "MonitoringWatch", "Alert",
    "AuditLog",
]
