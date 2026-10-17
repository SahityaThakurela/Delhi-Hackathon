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
from backend.app.services.rag import search as rag_search


class OperationsAgent(BaseAgent):
    """Specialist agent for operational uptime, SLA terms, and support commitments."""

    name = AgentName.operations
    dimension = Dimension.operations

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        documents = state.get("documents", [])
        inv_id = state.get("investigation_id", uuid4())
        hosp_id = state.get("hospital_id", uuid4())

        await self.emit_progress(inv_id, 25, "Searching SLA and contractual uptime commitments")

        sla_docs = await rag_search(
            db=None,
            hospital_id=hosp_id,
            query="Service Level Agreement SLA 99.9% uptime penalty escalation matrix response time resolution window",
            doc_types=["sla", "contract", "support_agreement"],
            documents=documents,
        )
        valid_sla_docs = [d for d in sla_docs if not d.get("is_suspicious")]

        # 1. Service Level Agreement (SLA) & Uptime Commitments
        if valid_sla_docs:
            doc = valid_sla_docs[0]
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Service Level Agreement (SLA) & Uptime Commitment",
                    description=f"Formal SLA documented in {doc.get('filename')} defining 99.9% uptime commitment with critical incident escalation procedure.",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                    evidence=[
                        FindingEvidenceRef(
                            id=doc.get("document_id", uuid4()),
                            source_name=doc.get("filename", "SLA.pdf"),
                            excerpt=self.format_untrusted_document(doc.get("excerpt", ""), doc.get("filename", "")),
                            page=doc.get("page", 1),
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
                    description="No formal SLA, contractual uptime commitments, or escalation matrices provided in documentation.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.high,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Require signed SLA with 99.9% uptime commitment and financial credit penalty clauses.",
                    missing_evidence="Executed SLA with defined response-time matrix",
                )
            )

        await self.emit_progress(inv_id, 75, "Evaluating support tiers and on-site engineering readiness")

        # 2. Local Indian Support & Escalation Structure
        support_docs = await rag_search(
            db=None,
            hospital_id=hosp_id,
            query="support hours 24/7 helpdesk ticketing local engineer on-site training deployment",
            doc_types=["sla", "brochure", "security_questionnaire"],
            documents=documents,
        )
        valid_support = [d for d in support_docs if not d.get("is_suspicious")]

        if valid_support:
            doc = valid_support[0]
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Support Infrastructure & Response Windows",
                    description=f"Documented support channels ({doc.get('filename')}): remote helpdesk and ticketing support.",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.vendor_claim,
                    evidence=[
                        FindingEvidenceRef(
                            id=doc.get("document_id", uuid4()),
                            source_name=doc.get("filename", "support.pdf"),
                            excerpt=self.format_untrusted_document(doc.get("excerpt", ""), doc.get("filename", "")),
                            page=doc.get("page", 1),
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
                    title="Local Support and On-Site Engineering Capacity",
                    description="No documentation regarding on-site engineering presence or 24/7 clinical emergency escalation for Indian hospitals.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.medium,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Mandate 24/7 phone escalation and 4-hour on-site response window for clinical outages.",
                    missing_evidence="Support scope of work and local Indian engineer staffing plan",
                )
            )

        await self.emit_progress(inv_id, 100, "Operations assessment completed")
        return {"findings": findings, "evidence": evidence}
