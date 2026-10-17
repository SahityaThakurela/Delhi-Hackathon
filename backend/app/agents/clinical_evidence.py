"""Clinical Evidence Specialist Agent (BE-6).

Investigates clinical claims, diagnostic decision support validations,
and queries ClinicalTrials.gov and PubMed E-utilities only when clinical algorithms are claimed.
"""

from typing import Any, Dict, List
from uuid import uuid4

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import FindingEvidenceRef, FindingItem, InvestigationState
from backend.app.agents.tools.clinical_trials import search_clinical_trials
from backend.app.agents.tools.pubmed import search_pubmed
from backend.app.schemas.ai_schemas import (
    AgentName,
    ClaimOrigin,
    Confidence,
    Dimension,
    FindingStatus,
    Severity,
)
from backend.app.services.rag import search as rag_search


class ClinicalEvidenceAgent(BaseAgent):
    """Specialist agent for clinical validation and algorithm evidence."""

    name = AgentName.clinical_evidence
    dimension = Dimension.clinical

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        product = state.get("product", {})
        documents = state.get("documents", [])
        inv_id = state.get("investigation_id", uuid4())
        hosp_id = state.get("hospital_id", uuid4())

        await self.emit_progress(inv_id, 15, "Checking for clinical and AI diagnostic claims")

        desc = str(product.get("description", "")).lower()
        claimed_standards = [str(s).lower() for s in product.get("claimed_standards", [])]

        clinical_keywords = [
            "diagnostic",
            "clinical ai",
            "triage",
            "decision support",
            "risk prediction",
            "cds",
            "algorithm",
            "machine learning diagnostic",
        ]

        has_clinical_claims = any(kw in desc for kw in clinical_keywords) or any(
            any(kw in s for kw in clinical_keywords) for s in claimed_standards
        )

        # RAG search for clinical documentation
        clinical_docs = await rag_search(
            db=None,
            hospital_id=hosp_id,
            query="clinical study trial validation algorithm sensitivity specificity AUC",
            doc_types=["clinical_study", "clinical_validation", "whitepaper"],
            documents=documents,
        )
        valid_clinical_docs = [d for d in clinical_docs if not d.get("is_suspicious")]

        # Rule: Return not_applicable if no clinical claims exist
        if not has_clinical_claims and not valid_clinical_docs:
            await self.emit_progress(inv_id, 100, "No clinical algorithms claimed; marked not_applicable")
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Clinical Decision Support / AI Algorithm Validation",
                    description="Product is an administrative and workflow system with no clinical decision support, diagnostic AI, or predictive triage algorithms claimed.",
                    status=FindingStatus.not_applicable,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                )
            )
            return {"findings": findings, "evidence": evidence}

        # If clinical claims exist, search PubMed & ClinicalTrials.gov
        await self.emit_progress(inv_id, 45, "Searching PubMed and ClinicalTrials.gov for prospective evidence")
        product_name = product.get("name", "Healthcare Software")
        vendor_name = state.get("vendor", {}).get("name", "")

        query_term = f"{product_name} clinical validation"
        ct_results = await search_clinical_trials(query=query_term)
        pm_results = await search_pubmed(query=f"{product_name} {vendor_name}")

        external_evidence: List[FindingEvidenceRef] = []

        if ct_results.get("status") == "found":
            for study in ct_results.get("studies", []):
                external_evidence.append(
                    FindingEvidenceRef(
                        source_name=f"ClinicalTrials.gov ({study.get('nct_id')})",
                        excerpt=f"Registered Trial: {study.get('title')} [Status: {study.get('status')}, Type: {study.get('study_type')}].",
                        is_independent=True,
                    )
                )

        if pm_results.get("status") == "found":
            for paper in pm_results.get("papers", []):
                external_evidence.append(
                    FindingEvidenceRef(
                        source_name=f"PubMed (PMID:{paper.get('pmid')})",
                        excerpt=f"Published Paper: {paper.get('title')}. URL: {paper.get('url')}",
                        is_independent=True,
                    )
                )

        # Include submitted document evidence
        doc_evidence: List[FindingEvidenceRef] = []
        for d in valid_clinical_docs:
            doc_evidence.append(
                FindingEvidenceRef(
                    id=d.get("document_id", uuid4()),
                    source_name=d.get("filename", "clinical_study.pdf"),
                    excerpt=self.format_untrusted_document(d.get("excerpt", ""), d.get("filename", "")),
                    page=d.get("page", 1),
                    is_independent=False,
                )
            )

        all_evidence = external_evidence + doc_evidence

        await self.emit_progress(inv_id, 80, "Synthesizing clinical trial and study evidence")

        if external_evidence:
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Independently Registered Clinical Trials / Publications",
                    description=f"Identified {len(external_evidence)} prospective clinical trial or peer-reviewed literature records validating clinical claims.",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                    evidence=external_evidence,
                )
            )
        elif doc_evidence:
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Vendor-Submitted Clinical Validation Study",
                    description=f"Vendor supplied internal or sponsored clinical evaluation report ({valid_clinical_docs[0].get('filename')}).",
                    status=FindingStatus.partially_supported,
                    severity=Severity.medium,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.vendor_claim,
                    recommended_action="Request independent hospital multi-center validation or peer-reviewed prospective study.",
                    evidence=doc_evidence,
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
                    title="Clinical Decision Support / AI Algorithm Validation",
                    description="Product claims clinical decision support or triage capabilities, but no independent peer-reviewed trials or PubMed literature could be verified.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.high,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.vendor_claim,
                    recommended_action="Require ICMR-approved prospective validation study or CE/FDA/CDSCO clinical evidence file.",
                    missing_evidence="Peer-reviewed prospective clinical trial report",
                )
            )

        await self.emit_progress(inv_id, 100, "Clinical evidence investigation finished")
        return {"findings": findings, "evidence": evidence}
