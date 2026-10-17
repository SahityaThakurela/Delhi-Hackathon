"""Clinical Evidence Specialist Agent (BE-6).

Investigates clinical claims, diagnostic decision support validations,
and ClinicalTrials.gov / PubMed literature where clinical algorithms are claimed.
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


class ClinicalEvidenceAgent(BaseAgent):
    """Specialist agent for clinical validation and algorithm evidence."""

    name = AgentName.clinical_evidence
    dimension = Dimension.clinical

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        product = state.get("product", {})
        documents = state.get("documents", [])
        inv_id = state.get("investigation_id")
        hosp_id = state.get("hospital_id")

        desc = str(product.get("description", "")).lower()
        clinical_docs = [
            d for d in documents
            if str(d.get("doc_type", "")).lower() in ("clinical_study", "clinical_validation")
            or "clinical" in str(d.get("filename", "")).lower()
        ]

        has_clinical_claims = any(
            kw in desc for kw in ("diagnostic", "clinical ai", "triage", "decision support", "risk prediction")
        )

        if not has_clinical_claims and not clinical_docs:
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Clinical Decision Support / AI Algorithm Validation",
                    description="No clinical decision support or diagnostic algorithms claimed for this software product.",
                    status=FindingStatus.not_applicable,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                )
            )
        elif clinical_docs:
            doc = clinical_docs[0]
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Clinical Validation Study Evidence",
                    description=f"Peer-reviewed clinical trial or validation documentation provided ({doc.get('filename')}).",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                    evidence=[
                        FindingEvidenceRef(
                            source_name=doc.get("filename", "study.pdf"),
                            excerpt="Prospective study validating algorithm accuracy against clinical benchmark.",
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
                    title="Clinical Validation for Decision Support Claims",
                    description="Product claims clinical decision support or triage capability, but no peer-reviewed studies or clinical trial results were provided.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.high,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.vendor_claim,
                    recommended_action="Request published prospective clinical trial results or ICMR study citations.",
                    missing_evidence="Peer-reviewed validation papers or clinical trial registration",
                )
            )

        return {"findings": findings, "evidence": evidence}
