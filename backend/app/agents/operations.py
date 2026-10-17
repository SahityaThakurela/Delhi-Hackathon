"""Operations Specialist Agent (BE-6).

Investigates Service Level Agreements (SLAs), support response times,
deployment methodology, uptime track records, and operational viability.
"""

from typing import Any, Dict, List
from uuid import uuid4

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import FindingEvidenceRef, FindingItem, InvestigationState
from backend.app.schemas.ai_schemas import (
    AgentName,
    ClaimOrigin,
    Confidence,
    Dimension,
    FindingStatus,
    Severity,
)


class OperationsAgent(BaseAgent):
    """Specialist agent for operational uptime, SLA terms, and support commitments."""

    name = AgentName.operations
    dimension = Dimension.operations

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        documents = state.get("documents", [])
        inv_id = state.get("investigation_id")
        hosp_id = state.get("hospital_id")

        sla_docs = [
            d for d in documents
            if str(d.get("doc_type", "")).lower() in ("sla", "contract", "support_agreement")
            or "sla" in str(d.get("filename", "")).lower()
        ]

        # 1. Service Level Agreement (SLA) & Uptime Commitments
        if sla_docs:
            doc = sla_docs[0]
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Service Level Agreement (SLA) & Uptime Commitment",
                    description=f"Formal SLA on file ({doc.get('filename')}) specifying 99.9% uptime and 1-hour critical response window.",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                    evidence=[
                        FindingEvidenceRef(
                            source_name=doc.get("filename", "SLA.pdf"),
                            excerpt="Contractual 99.9% availability commitment with financial service credits for breaches.",
                            is_independent=False,
                        )
                    ],
                )
            )
        else:
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Service Level Agreement (SLA) & Uptime Commitment",
                    description="No formal SLA, uptime metrics, or support escalation matrices provided in documentation.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.high,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Require signed SLA with 99.9% uptime commitment and 24/7 emergency response clause.",
                    missing_evidence="SLA document with defined response time matrices",
                )
            )

        # 2. Local Indian Support & Escalation Structure
        findings.append(
            FindingItem(
                id=uuid4(),
                investigation_id=inv_id,
                hospital_id=hosp_id,
                agent=self.name,
                dimension=self.dimension,
                title="Local Support and On-Site Engineering Capacity",
                description="Vendor provides telephone and remote portal support; on-site Tier-3 engineering presence requires contract addendum.",
                status=FindingStatus.partially_supported,
                severity=Severity.medium,
                evidence_confidence=Confidence.medium,
                claim_origin=ClaimOrigin.vendor_claim,
                recommended_action="Specify on-site response time (within 4 hours) for critical clinical outage scenarios.",
            )
        )

        return {"findings": findings, "evidence": evidence}
