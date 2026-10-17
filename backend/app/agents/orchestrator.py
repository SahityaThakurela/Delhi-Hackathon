"""LangGraph Orchestrator for Multi-Agent Investigation Swarm (BE-6).

Orchestrates parallel specialist agents, skeptic challenges, deterministic scoring,
and synthesis with LangGraph state checkpointing and dynamic steering.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.app.agents.clinical_evidence import ClinicalEvidenceAgent
from backend.app.agents.compliance import ComplianceAgent
from backend.app.agents.financial import FinancialAgent
from backend.app.agents.integration_fit import IntegrationFitAgent
from backend.app.agents.operations import OperationsAgent
from backend.app.agents.security_privacy import SecurityPrivacyAgent
from backend.app.agents.skeptic import SkepticAgent
from backend.app.agents.state import (
    InvestigationState,
    TimelineEventItem,
)
from backend.app.schemas.ai_schemas import (
    AgentName,
    Dimension,
    InvStatus,
    Severity,
)
from backend.app.services.scoring import compute_trust_score

logger = logging.getLogger(__name__)


# =====================================================================
# Node Implementation Functions
# =====================================================================

async def orchestrator_plan_node(state: InvestigationState) -> Dict[str, Any]:
    """Orchestrator planner node: initializes agent runs and plan timeline."""
    inv_id = state.get("investigation_id", uuid4())
    selected_dims = state.get("selected_dimensions") or list(Dimension)

    agent_runs = dict(state.get("agent_runs", {}))
    timeline = list(state.get("timeline_events", []))

    # Initialize runs for active dimensions
    active_agents = [
        AgentName.compliance,
        AgentName.clinical_evidence,
        AgentName.security_privacy,
        AgentName.financial,
        AgentName.integration_fit,
        AgentName.operations,
        AgentName.skeptic,
    ]

    for ag in active_agents:
        agent_runs[ag.value] = {
            "agent": ag,
            "status": "queued",
            "progress": 0,
            "current_task": "Queued for parallel execution",
        }

    timeline.append(
        TimelineEventItem(
            seq=len(timeline) + 1,
            event="investigation.planned",
            agent=AgentName.orchestrator,
            payload={
                "selected_dimensions": [d.value for d in selected_dims],
                "active_agents": [ag.value for ag in active_agents],
            },
        )
    )

    return {
        "status": InvStatus.running,
        "agent_runs": agent_runs,
        "timeline_events": timeline,
    }


async def compliance_node(state: InvestigationState) -> Dict[str, Any]:
    agent = ComplianceAgent()
    return await agent.run(state)


async def clinical_evidence_node(state: InvestigationState) -> Dict[str, Any]:
    agent = ClinicalEvidenceAgent()
    return await agent.run(state)


async def security_privacy_node(state: InvestigationState) -> Dict[str, Any]:
    agent = SecurityPrivacyAgent()
    return await agent.run(state)


async def financial_node(state: InvestigationState) -> Dict[str, Any]:
    agent = FinancialAgent()
    return await agent.run(state)


async def integration_fit_node(state: InvestigationState) -> Dict[str, Any]:
    agent = IntegrationFitAgent()
    return await agent.run(state)


async def operations_node(state: InvestigationState) -> Dict[str, Any]:
    agent = OperationsAgent()
    return await agent.run(state)


async def skeptic_node(state: InvestigationState) -> Dict[str, Any]:
    agent = SkepticAgent()
    return await agent.run(state)


async def synthesizer_node(state: InvestigationState) -> Dict[str, Any]:
    """Synthesizer node: runs deterministic scoring, generates summary, completes run."""
    inv_id = state.get("investigation_id", uuid4())
    findings = state.get("findings", [])
    hosp_profile = state.get("hospital_profile", {})
    risk_appetite = hosp_profile.get("risk_appetite", "balanced")
    timeline = list(state.get("timeline_events", []))

    # Compute deterministic trust score
    trust_score = compute_trust_score(
        investigation_id=inv_id,
        findings=findings,
        risk_appetite=risk_appetite,
    )

    # Count findings by severity
    crit_count = sum(1 for f in findings if f.severity == Severity.critical)
    high_count = sum(1 for f in findings if f.severity == Severity.high)
    med_count = sum(1 for f in findings if f.severity == Severity.medium)

    summary_text = (
        f"Investigation completed with {len(findings)} verified findings "
        f"({crit_count} critical, {high_count} high, {med_count} medium). "
        f"Overall Trust Score: {trust_score.overall_score}/100 "
        f"(Confidence: {round((trust_score.score_confidence or 0.0) * 100, 1)}%, "
        f"Overall Risk: {trust_score.overall_risk.value if trust_score.overall_risk else 'unknown'}). "
        f"Platform decision-support: human reviewer maintains final procurement authority."
    )

    timeline.append(
        TimelineEventItem(
            seq=len(timeline) + 1,
            event="investigation.completed",
            agent=AgentName.orchestrator,
            payload={
                "overall_score": trust_score.overall_score,
                "score_confidence": trust_score.score_confidence,
                "overall_risk": trust_score.overall_risk.value if trust_score.overall_risk else None,
                "findings_count": len(findings),
            },
        )
    )

    return {
        "status": InvStatus.completed,
        "overall_score": trust_score.overall_score,
        "score_confidence": trust_score.score_confidence,
        "overall_risk": trust_score.overall_risk,
        "summary": summary_text,
        "timeline_events": timeline,
    }


# =====================================================================
# StateGraph Builder & Checkpointing
# =====================================================================

def build_investigation_graph(checkpointer: Optional[Any] = None) -> StateGraph:
    """Build and compile the LangGraph multi-agent investigation workflow."""
    builder = StateGraph(InvestigationState)

    # 1. Register Nodes
    builder.add_node("orchestrator", orchestrator_plan_node)
    builder.add_node("compliance", compliance_node)
    builder.add_node("clinical_evidence", clinical_evidence_node)
    builder.add_node("security_privacy", security_privacy_node)
    builder.add_node("financial", financial_node)
    builder.add_node("integration_fit", integration_fit_node)
    builder.add_node("operations", operations_node)
    builder.add_node("skeptic", skeptic_node)
    builder.add_node("synthesizer", synthesizer_node)

    # 2. Edges: Start -> Orchestrator Plan
    builder.add_edge(START, "orchestrator")

    # 3. Parallel Fan-Out: Orchestrator -> 6 Specialist Agents
    builder.add_edge("orchestrator", "compliance")
    builder.add_edge("orchestrator", "clinical_evidence")
    builder.add_edge("orchestrator", "security_privacy")
    builder.add_edge("orchestrator", "financial")
    builder.add_edge("orchestrator", "integration_fit")
    builder.add_edge("orchestrator", "operations")

    # 4. Fan-In to Skeptic: Runs AFTER all specialist agents have completed
    builder.add_edge("compliance", "skeptic")
    builder.add_edge("clinical_evidence", "skeptic")
    builder.add_edge("security_privacy", "skeptic")
    builder.add_edge("financial", "skeptic")
    builder.add_edge("integration_fit", "skeptic")
    builder.add_edge("operations", "skeptic")

    # 5. Skeptic -> Synthesizer -> END
    builder.add_edge("skeptic", "synthesizer")
    builder.add_edge("synthesizer", END)

    # Compile with memory checkpointing for pause/resume/replay
    saver = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=saver)


# =====================================================================
# Steering Command Interpreter
# =====================================================================

def parse_steering_instruction(instruction: str) -> Dict[str, Any]:
    """Parse human steering command. Rejects instructions that attempt to bypass evidence rules."""
    lower = instruction.lower().strip()

    # Reject commands trying to bypass evidence rules or force compliance
    bypass_phrases = [
        "mark as compliant",
        "ignore findings",
        "certify vendor",
        "bypass evidence",
        "override rules",
        "mark as supported",
    ]
    for phrase in bypass_phrases:
        if phrase in lower:
            raise ValueError(f"Steering instruction rejected: cannot bypass evidence rules ('{phrase}').")

    prioritise = []
    deprioritise = []

    if "abdm" in lower:
        prioritise.append("abdm_v3")
    if "residency" in lower or "data residency" in lower:
        prioritise.append("data_residency")
    if "security" in lower:
        prioritise.append("security_privacy")
    if "clinical" in lower and "skip" in lower:
        deprioritise.append("clinical")

    return {
        "instruction": instruction,
        "prioritise": prioritise,
        "deprioritise": deprioritise,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
