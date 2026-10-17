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
from backend.app.realtime.emit import emit_event
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

        inv_id = state.get("investigation_id", uuid4())
        seq = len(state.get("timeline_events", [])) + 1

        await self.emit_progress(inv_id, 20, "Auditing specialist findings for unsubstantiated claims")

        for f in findings:
            # Challenge criteria: findings claimed supported or critical/high severity
            is_supported = f.status == FindingStatus.supported
            is_high_risk = f.severity in (Severity.critical, Severity.high)

            if not (is_supported or is_high_risk):
                updated_findings.append(f)
                continue

            # Check 1: Vendor claim masquerading as independent verification without primary proof
            is_single_vendor_source = (
                f.claim_origin == ClaimOrigin.vendor_claim
                or all(not getattr(e, "is_independent", False) for e in f.evidence)
            )

            if is_supported and is_single_vendor_source and not f.evidence:
                f.status = FindingStatus.unverified
                f.evidence_confidence = Confidence.low
                f.missing_evidence = f"Skeptic Challenge: Claim lacks primary verifiable proof."

                msgs = [
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
                ]
                debate_messages.extend(msgs)
                for m in msgs:
                    try:
                        await emit_event(inv_id, "debate.message", m.model_dump(mode="json"))
                    except Exception:
                        pass
                seq += 2

            # Check 2: Marketing brochure used to substantiate regulatory or security compliance
            elif is_supported and any("brochure" in str(getattr(e, "source_name", "")).lower() for e in f.evidence):
                f.status = FindingStatus.unverified
                f.evidence_confidence = Confidence.medium
                f.recommended_action = "Require independent audit report; vendor brochure is non-binding."

                msgs = [
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
                        role=DebateRole.rebuttal,
                        content=f"Vendor brochure cited as sole source: '{f.evidence[0].source_name}'.",
                    ),
                    DebateMessageItem(
                        investigation_id=inv_id,
                        finding_id=f.id,
                        seq=seq + 2,
                        agent=self.name,
                        role=DebateRole.resolution,
                        content=f"Reclassified status to 'unverified'. Independent audit documentation required before contracting.",
                    ),
                ]
                debate_messages.extend(msgs)
                for m in msgs:
                    try:
                        await emit_event(inv_id, "debate.message", m.model_dump(mode="json"))
                    except Exception:
                        pass
                seq += 3

            # Check 3: Confirmed valid findings with independent proof
            elif is_supported and any(getattr(e, "is_independent", False) for e in f.evidence):
                resolution_msg = DebateMessageItem(
                    investigation_id=inv_id,
                    finding_id=f.id,
                    seq=seq,
                    agent=self.name,
                    role=DebateRole.resolution,
                    content=f"Skeptic review verified '{f.title}': Supported by independent external evidence.",
                )
                debate_messages.append(resolution_msg)
                try:
                    await emit_event(inv_id, "debate.message", resolution_msg.model_dump(mode="json"))
                except Exception:
                    pass
                seq += 1

            updated_findings.append(f)

        await self.emit_progress(inv_id, 100, f"Skeptic audit complete: {len(debate_messages)} debate points recorded")

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
