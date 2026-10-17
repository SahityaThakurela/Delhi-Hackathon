"""Security & Privacy Specialist Agent (BE-6).

Investigates ISO 27001 certifications, VAPT report recency, encryption controls,
NVD CVE vulnerability history (with 24h Redis caching), and Indian data residency compliance.
"""

from typing import Any, Dict, List
from uuid import uuid4

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import FindingEvidenceRef, FindingItem, InvestigationState
from backend.app.agents.tools.nvd import lookup_cves
from backend.app.schemas.ai_schemas import (
    AgentName,
    ClaimOrigin,
    Confidence,
    Dimension,
    FindingStatus,
    Severity,
)
from backend.app.services.deterministic import cert_valid, report_recent, residency_check
from backend.app.services.rag import search as rag_search


class SecurityPrivacyAgent(BaseAgent):
    """Specialist agent for cybersecurity, vulnerability posture, and data protection."""

    name = AgentName.security_privacy
    dimension = Dimension.security_privacy

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        product = state.get("product", {})
        vendor = state.get("vendor", {})
        documents = state.get("documents", [])
        hosp_profile = state.get("hospital_profile", {})
        inv_id = state.get("investigation_id", uuid4())
        hosp_id = state.get("hospital_id", uuid4())

        await self.emit_progress(inv_id, 20, "Executing deterministic ISO 27001 and VAPT checks")

        # 1. ISO 27001 Certificate Validity Check
        iso_docs = await rag_search(
            db=None,
            hospital_id=hosp_id,
            query="ISO 27001 ISMS information security management certificate accreditation validity",
            doc_types=["iso27001_cert", "cert", "security_cert"],
            documents=documents,
        )
        valid_iso_docs = [d for d in iso_docs if not d.get("is_suspicious")]

        if valid_iso_docs:
            iso_doc = valid_iso_docs[0]
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
                            id=iso_doc.get("document_id", uuid4()),
                            source_name=iso_doc.get("filename", "ISO27001_cert.pdf"),
                            excerpt=f"Validity evaluation: {cert_res.detail}",
                            page=iso_doc.get("page", 1),
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
                    description="No ISO 27001 certificate provided in vendor evidence submission.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.high,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Request vendor's ISO/IEC 27001 accredited certificate.",
                    missing_evidence="ISO 27001 certificate with active surveillance endorsement",
                )
            )

        await self.emit_progress(inv_id, 45, "Validating VAPT report recency (365-day threshold)")

        # 2. VAPT Report Recency Check
        vapt_docs = await rag_search(
            db=None,
            hospital_id=hosp_id,
            query="VAPT vulnerability assessment penetration testing security audit executive summary",
            doc_types=["vapt_report", "security_audit", "audit_report"],
            documents=documents,
        )
        valid_vapt_docs = [d for d in vapt_docs if not d.get("is_suspicious")]

        if valid_vapt_docs:
            vapt_doc = valid_vapt_docs[0]
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
                            id=vapt_doc.get("document_id", uuid4()),
                            source_name=vapt_doc.get("filename", "VAPT_report.pdf"),
                            excerpt=f"VAPT report evaluation: {vapt_res.detail}",
                            page=vapt_doc.get("page", 1),
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
                    recommended_action="Obtain CERT-In empaneled auditor penetration testing report.",
                    missing_evidence="Annual third-party VAPT audit report",
                )
            )

        await self.emit_progress(inv_id, 70, "Querying NVD CVE vulnerability records with 24h caching")

        # 3. NVD CVE Lookup with 24-hour cache
        vendor_name = vendor.get("name", "")
        product_name = product.get("name", "")
        nvd_res = await lookup_cves(vendor_name=vendor_name, product_name=product_name)

        if nvd_res.get("status") == "vulnerabilities_found":
            cves = nvd_res.get("cves", [])
            highest_score = max((c.get("base_score", 0.0) for c in cves), default=0.0)
            sev = Severity.critical if highest_score >= 9.0 else Severity.high if highest_score >= 7.0 else Severity.medium

            cve_evidence = [
                FindingEvidenceRef(
                    source_name=f"NVD CVE: {c.get('cve_id')}",
                    excerpt=f"{c.get('description')} (CVSS: {c.get('base_score')})",
                    is_independent=True,
                )
                for c in cves
            ]
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title=f"National Vulnerability Database (NVD) CVE Records ({len(cves)} found)",
                    description=f"Identified {len(cves)} public CVE vulnerabilities (max CVSS score {highest_score}).",
                    status=FindingStatus.contradictory,
                    severity=sev,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                    recommended_action="Demand remediation patch logs and proof of mitigation for identified CVEs.",
                    evidence=cve_evidence,
                )
            )
        elif nvd_res.get("status") == "clean":
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="NVD Public CVE Vulnerability History",
                    description=f"No known unpatched CVEs found in NVD for '{product_name}' by '{vendor_name}'.",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                )
            )
        else:
            # Service unavailable: handle gracefully without failing
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="NVD Public CVE Vulnerability History",
                    description="NVD CVE lookup service temporarily unavailable. Fallback to manual CERT-In/NVD review.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.low,
                    evidence_confidence=Confidence.low,
                    claim_origin=ClaimOrigin.inferred,
                )
            )

        await self.emit_progress(inv_id, 90, "Evaluating Indian data residency constraints")

        # 4. Indian Data Residency Policy Check
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

        await self.emit_progress(inv_id, 100, "Security & privacy investigation completed")
        return {"findings": findings, "evidence": evidence}
