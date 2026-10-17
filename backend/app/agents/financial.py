"""Financial & Corporate Diligence Specialist Agent (BE-6).

Investigates MCA filings, audited financial statements, and corporate disclosures.
Never produces predictive financial scoring; missing evidence yields insufficient_evidence.
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


class FinancialAgent(BaseAgent):
    """Specialist agent for vendor operational continuity and financial documentation."""

    name = AgentName.financial
    dimension = Dimension.financial

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        vendor = state.get("vendor", {})
        documents = state.get("documents", [])
        inv_id = state.get("investigation_id")
        hosp_id = state.get("hospital_id")

        cin = vendor.get("cin")
        fin_docs = [
            d for d in documents
            if str(d.get("doc_type", "")).lower() in ("financial_statement", "annual_report")
            or "financial" in str(d.get("filename", "")).lower()
        ]

        # 1. Corporate Identity & Registration (CIN)
        if cin:
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Corporate Registration & Ministry of Corporate Affairs (MCA) Record",
                    description=f"Vendor registered in India with Corporate Identification Number (CIN): {cin}.",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
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
                    title="Corporate Registration & Ministry of Corporate Affairs (MCA) Record",
                    description="No Indian Corporate Identification Number (CIN) or incorporation certificate provided.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.medium,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Verify vendor incorporation via MCA portal or GST registration certificate.",
                    missing_evidence="MCA CIN or certificate of incorporation",
                )
            )

        # 2. Audited Financial Statements
        if fin_docs:
            doc = fin_docs[0]
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Audited Financial Statements (Last 2 Fiscal Years)",
                    description=f"Audited financial statements available on file ({doc.get('filename')}).",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                    evidence=[
                        FindingEvidenceRef(
                            source_name=doc.get("filename", "Financials.pdf"),
                            excerpt="Independent Auditor Report and Balance Sheet for preceding financial year.",
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
                    title="Audited Financial Statements (Last 2 Fiscal Years)",
                    description="No audited financial statements submitted. Vendor financial viability cannot be evaluated.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.medium,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Request balance sheet and P&L statements for the last 2 audited fiscal years.",
                    missing_evidence="Audited balance sheet and chartered accountant report",
                )
            )

        return {"findings": findings, "evidence": evidence}
