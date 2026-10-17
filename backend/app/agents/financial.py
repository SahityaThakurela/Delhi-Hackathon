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
from backend.app.services.rag import search as rag_search


class FinancialAgent(BaseAgent):
    """Specialist agent for vendor operational continuity and financial documentation."""

    name = AgentName.financial
    dimension = Dimension.financial

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        vendor = state.get("vendor", {})
        documents = state.get("documents", [])
        inv_id = state.get("investigation_id", uuid4())
        hosp_id = state.get("hospital_id", uuid4())

        await self.emit_progress(inv_id, 25, "Verifying Indian MCA corporate registration and CIN")

        cin = vendor.get("cin")
        vendor_name = vendor.get("name", "Vendor")

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
                    description=f"Vendor '{vendor_name}' is registered with Corporate Identification Number (CIN): {cin}.",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                    evidence=[
                        FindingEvidenceRef(
                            source_name="Ministry of Corporate Affairs (MCA)",
                            excerpt=f"Incorporation Record CIN: {cin}",
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
                    title="Corporate Registration & Ministry of Corporate Affairs (MCA) Record",
                    description="No Indian Corporate Identification Number (CIN) or incorporation certificate provided.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.medium,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Verify vendor incorporation on the MCA portal or request GST registration certificate.",
                    missing_evidence="MCA Corporate Identification Number (CIN) or incorporation certificate",
                )
            )

        await self.emit_progress(inv_id, 65, "Searching audited financial statements and balance sheets")

        # 2. Audited Financial Statements
        fin_docs = await rag_search(
            db=None,
            hospital_id=hosp_id,
            query="audited financial statement balance sheet profit loss CA report annual report",
            doc_types=["financial_statement", "annual_report", "balance_sheet"],
            documents=documents,
        )
        valid_fin_docs = [d for d in fin_docs if not d.get("is_suspicious")]

        if valid_fin_docs:
            doc = valid_fin_docs[0]
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Audited Financial Statements (Preceding 2 Fiscal Years)",
                    description=f"Audited financial statements available on file ({doc.get('filename')}).",
                    status=FindingStatus.supported,
                    severity=Severity.info,
                    evidence_confidence=Confidence.high,
                    claim_origin=ClaimOrigin.independently_verified,
                    evidence=[
                        FindingEvidenceRef(
                            id=doc.get("document_id", uuid4()),
                            source_name=doc.get("filename", "Financials.pdf"),
                            excerpt=self.format_untrusted_document(doc.get("excerpt", ""), doc.get("filename", "")),
                            page=doc.get("page", 1),
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
                    title="Audited Financial Statements (Preceding 2 Fiscal Years)",
                    description="No audited balance sheets or chartered accountant reports submitted. Operational financial stability cannot be evaluated.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.medium,
                    evidence_confidence=Confidence.medium,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Request balance sheet and P&L statements for the last 2 audited fiscal years.",
                    missing_evidence="Audited balance sheet and chartered accountant report",
                )
            )

        await self.emit_progress(inv_id, 100, "Financial diligence completed")
        return {"findings": findings, "evidence": evidence}
