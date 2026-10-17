"""Security & Privacy Specialist Agent (BE-6).

Investigates ISO 27001 certifications, VAPT report recency, encryption controls,
NVD CVE records, and Indian data residency compliance.
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
from backend.app.services.deterministic import cert_valid, report_recent, residency_check


class SecurityPrivacyAgent(BaseAgent):
    """Specialist agent for cybersecurity, vulnerability posture, and data protection."""

    name = AgentName.security_privacy
    dimension = Dimension.security_privacy

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        product = state.get("product", {})
        documents = state.get("documents", [])
        hosp_profile = state.get("hospital_profile", {})
        inv_id = state.get("investigation_id")
        hosp_id = state.get("hospital_id")

        # 1. ISO 27001 Certification Validity Check
        iso_docs = [
            d for d in documents
            if "iso27001" in str(d.get("doc_type", "")).lower() or "iso" in str(d.get("filename", "")).lower()
        ]
        if iso_docs:
            iso_doc = iso_docs[0]
            cert_res = cert_valid(iso_doc)
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="ISO 27001 Information Security Management Certification",
                    description=cert_res.detail,
                    status=cert_res.status,
                    severity=cert_res.severity_hint,
                    evidence_confidence=Confidence.high,
                    claim_origin=cert_res.origin,
                    recommended_action="Request renewed certificate or latest surveillance audit report." if cert_res.status == FindingStatus.contradictory else None,
                    evidence=[
                        FindingEvidenceRef(
                            source_name=iso_doc.get("filename", "ISO27001_cert.pdf"),
                            excerpt=f"Validity evaluation: {cert_res.detail}",
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
                    title="ISO 27001 Information Security Management Certification",
                    description="No ISO 27001 certification provided on file.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.high,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Request vendor's ISO/IEC 27001 certificate with active surveillance endorsement.",
                    missing_evidence="ISO 27001 accredited certificate",
                )
            )

        # 2. VAPT Report Recency Check
        vapt_docs = [
            d for d in documents
            if "vapt" in str(d.get("doc_type", "")).lower() or "vapt" in str(d.get("filename", "")).lower()
        ]
        if vapt_docs:
            vapt_doc = vapt_docs[0]
            vapt_res = report_recent(vapt_doc, max_age_days=365)
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Vulnerability Assessment and Penetration Testing (VAPT) Recency",
                    description=vapt_res.detail,
                    status=vapt_res.status,
                    severity=vapt_res.severity_hint,
                    evidence_confidence=Confidence.high,
                    claim_origin=vapt_res.origin,
                    recommended_action="Request fresh CERT-In empaneled third-party VAPT report." if vapt_res.status == FindingStatus.contradictory else None,
                    evidence=[
                        FindingEvidenceRef(
                            source_name=vapt_doc.get("filename", "VAPT_report.pdf"),
                            excerpt=f"VAPT report evaluation: {vapt_res.detail}",
                            is_independent=True,
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
                    title="Vulnerability Assessment and Penetration Testing (VAPT) Recency",
                    description="No third-party VAPT report provided in vendor submission.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.high,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Obtain CERT-In empaneled auditor penetration testing executive summary.",
                    missing_evidence="Annual third-party VAPT audit report",
                )
            )

        # 3. Data Residency in India Check
        policy = hosp_profile.get("data_residency", "india_only")
        dep_models = product.get("deployment_models", ["public_cloud"])
        residency_res = residency_check(dep_models, data_residency_policy=policy, documents=documents)
        findings.append(
            FindingItem(
                id=uuid4(),
                investigation_id=inv_id,
                hospital_id=hosp_id,
                agent=self.name,
                dimension=self.dimension,
                title="Data Residency Policy Compliance (India Only)",
                description=residency_res.detail,
                status=residency_res.status,
                severity=residency_res.severity_hint,
                evidence_confidence=Confidence.medium,
                claim_origin=residency_res.origin,
                recommended_action="Require contract clause mandating all clinical and PII data reside within MeitY-empaneled Indian data centers." if residency_res.status != FindingStatus.supported else None,
            )
        )

        return {"findings": findings, "evidence": evidence}
