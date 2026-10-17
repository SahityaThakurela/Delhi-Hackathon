"""Compliance Specialist Agent (BE-6).

Investigates regulatory compliance, ABDM v3, DPDP Act 2023, NABH digital-health,
and CDSCO licensing applicability.
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
from backend.app.services.deterministic import abdm_checks
from backend.app.services.rag import search as rag_search


class ComplianceAgent(BaseAgent):
    """Specialist agent for healthcare IT regulatory & certification compliance."""

    name = AgentName.compliance
    dimension = Dimension.compliance

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        product = state.get("product", {})
        documents = state.get("documents", [])
        inv_id = state.get("investigation_id", uuid4())
        hosp_id = state.get("hospital_id", uuid4())

        await self.emit_progress(inv_id, 20, "Executing deterministic ABDM and regulatory checks")

        # 1. Deterministic ABDM v3 API Check
        abdm_res = abdm_checks(product, documents)
        abdm_evidence = []
        for ref in abdm_res.evidence_refs:
            abdm_evidence.append(
                FindingEvidenceRef(
                    id=ref,
                    source_name="ABDM Compliance Record",
                    excerpt="ABDM v3 sandbox/milestone certification",
                    is_independent=True,
                )
            )

        findings.append(
            FindingItem(
                id=uuid4(),
                investigation_id=inv_id,
                hospital_id=hosp_id,
                agent=self.name,
                dimension=self.dimension,
                title="ABDM v3 (Ayushman Bharat Digital Mission) Compliance",
                description=abdm_res.detail,
                status=abdm_res.status,
                severity=abdm_res.severity_hint,
                evidence_confidence=Confidence.high if abdm_evidence else Confidence.medium,
                claim_origin=abdm_res.origin,
                recommended_action="Require ABDM sandbox integration test report prior to final contract signing.",
                missing_evidence="Official ABDM milestone certificate or sandbox test logs" if abdm_res.status != FindingStatus.supported else None,
                evidence=abdm_evidence,
            )
        )

        await self.emit_progress(inv_id, 50, "Searching DPDP Act 2023 evidence")

        # 2. RAG Evidence Retrieval for DPDP Act 2023
        rag_hits = await rag_search(
            db=None,
            hospital_id=hosp_id,
            query="DPDP Act 2023 privacy consent breach notification CERT-In data fiduciary",
            doc_types=["dpdp_policy", "security_questionnaire", "privacy_policy"],
            documents=documents,
        )

        # Exclude suspicious prompt injection chunks from normal reasoning per Rule 14
        valid_hits = [h for h in rag_hits if not h.get("is_suspicious")]
        suspicious_hits = [h for h in rag_hits if h.get("is_suspicious")]

        if valid_hits:
            hit = valid_hits[0]
            dpdp_ev = FindingEvidenceRef(
                id=hit.get("document_id", uuid4()),
                source_name=hit.get("filename", "dpdp_policy.pdf"),
                excerpt=self.format_untrusted_document(hit.get("excerpt", ""), hit.get("filename", "")),
                page=hit.get("page", 1),
                is_independent=False,
            )
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="DPDP Act 2023 Consent & Breach Notification Process",
                    description="Vendor has submitted documented data protection policy aligned with Digital Personal Data Protection Act 2023.",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.vendor_claim,
                    evidence=[dpdp_ev],
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
                    title="DPDP Act 2023 Consent & Breach Notification Process",
                    description="No documented DPDP Act 2023 compliance policy or breach notification protocol was provided.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.high,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Request vendor's formal DPDP 2023 policy and CERT-In breach escalation matrix.",
                    missing_evidence="DPDP policy and data processing agreement (DPA)",
                )
            )

        # Record prompt injection finding if suspicious content was caught
        if suspicious_hits:
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Possible prompt-injection content in vendor document",
                    description=f"Detected instruction-like override patterns in {suspicious_hits[0].get('filename')}. Excluded from reasoning.",
                    status=FindingStatus.unverified,
                    severity=Severity.low,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Audit vendor document for adversarial prompt injection text.",
                )
            )

        await self.emit_progress(inv_id, 80, "Evaluating CDSCO SaMD and NABH digital-health requirements")

        # 3. CDSCO Medical Device Rules Applicability Check
        category = product.get("category", "")
        if category in ("his_emr", "billing", "erp", "lis"):
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="CDSCO Medical Device Rules Applicability",
                    description=f"Product category '{category}' is general administrative/workflow IT, not designated as Software as a Medical Device (SaMD) under CDSCO Rules 2017.",
                    status=FindingStatus.not_applicable,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                )
            )

        await self.emit_progress(inv_id, 100, "Compliance assessment completed")
        return {"findings": findings, "evidence": evidence}
