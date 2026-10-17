"""Typed Investigation State definition for LangGraph orchestrator (BE-6).

Strictly typed state models per Section 4, 5, and BE-6 of the Kyro Team Build Bible.
Includes reducers for parallel agent fan-out and fan-in execution.
"""

from datetime import datetime, timezone
from operator import add
from typing import Annotated, Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from backend.app.schemas.ai_schemas import (
    AgentName,
    ClaimOrigin,
    Confidence,
    DebateRole,
    Dimension,
    FindingStatus,
    InvStatus,
    ReviewDecision,
    Severity,
)


# =====================================================================
# Pydantic Domain Sub-Models
# =====================================================================

class FindingEvidenceRef(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    relation: str = Field(default="supports", description="'supports' | 'contradicts' | 'context'")
    source_type: str = "vendor_document"
    source_name: str
    page: Optional[int] = None
    excerpt: str
    doc_version: Optional[str] = None
    source_date: Optional[str] = None
    is_independent: bool = False


class FindingItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    hospital_id: UUID
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
    evidence: List[FindingEvidenceRef] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DebateMessageItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    finding_id: Optional[UUID] = None
    seq: int = 1
    agent: AgentName
    role: DebateRole
    content: str
    evidence_ids: List[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TimelineEventItem(BaseModel):
    seq: int
    event: str
    agent: Optional[AgentName] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentRunItem(BaseModel):
    agent: AgentName
    status: str = "pending"  # pending, running, completed, failed, skipped
    progress: int = 0
    current_task: Optional[str] = None
    error: Optional[str] = None
    findings_count: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


# =====================================================================
# Reducer Functions for Parallel Fan-Out / Fan-In
# =====================================================================

def merge_agent_runs(current: Dict[str, Dict[str, Any]], update: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Merge dictionary of agent runs."""
    merged = dict(current or {})
    if update:
        for k, v in update.items():
            if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
                merged[k] = {**merged[k], **v}
            else:
                merged[k] = v
    return merged


def merge_findings(current: List[FindingItem], update: List[FindingItem]) -> List[FindingItem]:
    """Merge findings, allowing updates to existing findings (e.g., from Skeptic)."""
    curr_list = list(current or [])
    if not update:
        return curr_list

    # Map existing findings by id
    by_id = {str(f.id): i for i, f in enumerate(curr_list)}

    for item in update:
        item_id = str(item.id)
        if item_id in by_id:
            curr_list[by_id[item_id]] = item
        else:
            curr_list.append(item)
            by_id[item_id] = len(curr_list) - 1

    return curr_list


def append_items(current: List[Any], update: List[Any]) -> List[Any]:
    """Append list items preserving order."""
    return (current or []) + (update or [])


# =====================================================================
# LangGraph Investigation State (TypedDict)
# =====================================================================

class InvestigationState(TypedDict, total=False):
    """Investigation state model passed across LangGraph nodes."""

    # Investigation & Entity Identifiers
    investigation_id: UUID
    hospital_id: UUID
    title: str

    # Hospital Profile & Requirements Context
    hospital_profile: Dict[str, Any]
    hospital_requirements: List[Dict[str, Any]]
    hospital_systems: List[Dict[str, Any]]

    # Vendor & Product Evidence Context
    vendor: Dict[str, Any]
    product: Dict[str, Any]
    documents: List[Dict[str, Any]]

    # Investigation Configuration & Steering
    selected_dimensions: List[Dimension]
    instructions: Optional[str]
    steering_commands: Annotated[List[Dict[str, Any]], append_items]

    # Dynamic Agent Runs & Lifecycle
    status: InvStatus
    agent_runs: Annotated[Dict[str, Dict[str, Any]], merge_agent_runs]

    # Findings & Evidence Accumulator
    findings: Annotated[List[FindingItem], merge_findings]
    evidence: Annotated[List[Dict[str, Any]], append_items]
    debate_messages: Annotated[List[DebateMessageItem], append_items]
    timeline_events: Annotated[List[TimelineEventItem], append_items]

    # Synthesis & Results
    dimension_scores: Dict[str, Any]
    overall_score: Optional[float]
    score_confidence: Optional[float]
    overall_risk: Optional[Severity]
    summary: Optional[str]

    # Errors & Resiliency
    errors: Annotated[List[Dict[str, Any]], append_items]
