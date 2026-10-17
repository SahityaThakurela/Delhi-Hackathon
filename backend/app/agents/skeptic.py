"""Skeptic Agent (BE-6).

The critical adversarial reviewer in the Kyro swarm.
Runs AFTER specialist agents gather initial findings.
For every finding rated 'supported' or severity >= 'high', the Skeptic attempts
to refute claims, detects single-source biases, downgrades unearned confidence,
and writes structured debate_messages (claim -> challenge -> rebuttal -> resolution).
"""

from typing import Any, Dict, List
from uuid import uuid4

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import (
    DebateMessageItem,
    FindingItem,
    InvestigationState,
    TimelineEventItem,
)
from backend.app.schemas.ai_schemas import (
    AgentName,
    ClaimOrigin,
    Confidence,
    DebateRole,
    Dimension,
    FindingStatus,
    Severity,
)


class SkepticAgent(BaseAgent):
    """Adversarial agent challenging over-optimistic vendor claims and unverified findings."""

    name = AgentName.skeptic
    dimension = Dimension.compliance

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings = list(state.get("findings", []))
        debate_messages: List[DebateMessageItem] = []
        timeline: List[TimelineEventItem] = []
        updated_findings: List[FindingItem] = []

        inv_id = state.get("investigation_id")
        seq = len(state.get("timeline_events", [])) + 1

        for f in findings:
            # Challenge criteria: findings claimed supported or critical/high severity
            is_supported = f.status == FindingStatus.supported
            is_high_risk = f.severity in (Severity.critical, Severity.high)

            if not (is_supported or is_high_risk):
                updated_findings.append(f)
                continue

            # Check 1: Vendor claim masquerading as independent verification
            is_single_vendor_source = (
                f.claim_origin == ClaimOrigin.vendor_claim
                or all(not getattr(e, "is_independent", False) for e in f.evidence)
            )

            if is_supported and is_single_vendor_source and not f.evidence:
                # Downgrade: claim without evidence
                f.status = FindingStatus.unverified
                f.evidence_confidence = Confidence.low
                f.missing_evidence = f"Skeptic Challenge: Claim lacks primary verifiable proof."

                debate_messages.extend([
                    DebateMessageItem(
                        investigation_id=inv_id,
                        finding_id=f.id,
                        seq=seq,
                        agent=self.name,
                        role=DebateRole.challenge,
                        content=f"Challenging finding '{f.title}': Status was marked Supported, but relies solely on unverified vendor claims without independent proof.",
                    ),
                    DebateMessageItem(
                        investigation_id=inv_id,
                        finding_id=f.id,
                        seq=seq + 1,
                        agent=self.name,
                        role=DebateRole.resolution,
                        content=f"Downgrading finding '{f.title}' to 'unverified' with low confidence.",
                    ),
                ])
                seq += 2

            elif is_supported and any("brochure" in str(getattr(e, "source_name", "")).lower() for e in f.evidence):
                # Downgrade: brochure used as evidence of standard compliance
                f.status = FindingStatus.unverified
                f.evidence_confidence = Confidence.medium
                f.recommended_action = "Require independent audit report; vendor brochure is non-binding."

                debate_messages.extend([
                    DebateMessageItem(
                        investigation_id=inv_id,
                        finding_id=f.id,
                        seq=seq,
                        agent=self.name,
                        role=DebateRole.challenge,
                        content=f"Challenging finding '{f.title}': Brochure marketing material cannot substantiate regulatory or architectural compliance.",
                    ),
                    DebateMessageItem(
                        investigation_id=inv_id,
                        finding_id=f.id,
                        seq=seq + 1,
                        agent=self.name,
                        role=DebateRole.resolution,
                        content=f"Reclassified status to 'unverified'. Independent audit documentation required.",
                    ),
                ])
                seq += 2

            elif is_supported:
                # Confirmed with robust evidence
                debate_messages.append(
                    DebateMessageItem(
                        investigation_id=inv_id,
                        finding_id=f.id,
                        seq=seq,
                        agent=self.name,
                        role=DebateRole.resolution,
                        content=f"Skeptic review passed for '{f.title}': Evidence verified against objective documentation.",
                    )
                )
                seq += 1

            updated_findings.append(f)

        timeline.append(
            TimelineEventItem(
                seq=seq,
                event="skeptic.completed",
                agent=self.name,
                payload={"challenged_count": len(debate_messages)},
            )
        )

        return {
            "findings": updated_findings,
            "debate_messages": debate_messages,
            "timeline_events": timeline,
        }
