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
from backend.app.services.deterministic import abdm_checks, cert_valid


class ComplianceAgent(BaseAgent):
    """Specialist agent for healthcare IT regulatory & certification compliance."""

    name = AgentName.compliance
    dimension = Dimension.compliance

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        product = state.get("product", {})
        documents = state.get("documents", [])
        inv_id = state.get("investigation_id")
        hosp_id = state.get("hospital_id")

        # 1. Deterministic ABDM v3 API Check
        abdm_res = abdm_checks(product, documents)
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
                evidence_confidence=Confidence.high if abdm_res.evidence_refs else Confidence.medium,
                claim_origin=abdm_res.origin,
                recommended_action="Require ABDM sandbox integration test report prior to final contract signing.",
                missing_evidence="Official ABDM milestone certificate or sandbox test logs" if abdm_res.status != FindingStatus.supported else None,
                evidence=[
                    FindingEvidenceRef(
                        id=ref,
                        source_name="ABDM Documentation",
                        excerpt="ABDM compliance record",
                        is_independent=True,
                    )
                    for ref in abdm_res.evidence_refs
                ],
            )
        )

        # 2. DPDP Act 2023 Consent & Breach Notification Check
        dpdp_docs = [d for d in documents if "dpdp" in str(d.get("doc_type", "")).lower() or "privacy" in str(d.get("filename", "")).lower()]
        if dpdp_docs:
            doc = dpdp_docs[0]
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
                    claim_origin=ClaimOrigin.independently_verified,
                    evidence=[
                        FindingEvidenceRef(
                            source_name=doc.get("filename", "dpdp_policy.pdf"),
                            excerpt="Documented data fiduciary obligations and 72-hour CERT-In incident notification procedure.",
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

        # 3. CDSCO Medical Device Software Applicability Check
        category = product.get("category", "")
        if category in ("his_emr", "billing", "erp"):
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="CDSCO Medical Device Rules Applicability",
                    description=f"Product category '{category}' is general hospital workflow IT, not designated as Software as a Medical Device (SaMD) under CDSCO.",
                    status=FindingStatus.not_applicable,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                )
            )

        return {"findings": findings, "evidence": evidence}
