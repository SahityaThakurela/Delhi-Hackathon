"""Integration Fit Specialist Agent (BE-6).

Hands off to the Integration Compatibility Engine (services/integration_engine.py)
and converts compatibility evaluations into structured evidence-backed findings.
"""

from typing import Any, Dict, List
from uuid import uuid4

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import FindingEvidenceRef, FindingItem, InvestigationState
from backend.app.schemas.ai_schemas import (
    AgentName,
    ClaimOrigin,
    CompatStatus,
    Confidence,
    Dimension,
    FindingStatus,
    Severity,
)
from backend.app.services.integration_engine import evaluate_integration_compatibility


class IntegrationFitAgent(BaseAgent):
    """Specialist agent assessing technical interoperability and infrastructure compatibility."""

    name = AgentName.integration_fit
    dimension = Dimension.integration

    async def investigate(self, state: InvestigationState) -> Dict[str, Any]:
        findings: List[FindingItem] = []
        evidence: List[Dict[str, Any]] = []

        hosp_systems = state.get("hospital_systems", [])
        product = state.get("product", {})
        inv_id = state.get("investigation_id", uuid4())
        hosp_id = state.get("hospital_id", uuid4())

        await self.emit_progress(inv_id, 25, "Cross-referencing hospital systems with vendor capabilities")

        compat = evaluate_integration_compatibility(hosp_systems, product)
        checks = compat.get("checks", [])

        if not checks:
            findings.append(
                FindingItem(
                    id=uuid4(),
                    investigation_id=inv_id,
                    hospital_id=hosp_id,
                    agent=self.name,
                    dimension=self.dimension,
                    title="Hospital System Integration Baseline",
                    description="No existing hospital systems registered for compatibility cross-referencing.",
                    status=FindingStatus.insufficient_evidence,
                    severity=Severity.medium,
                    evidence_confidence=Confidence.low,
                    claim_origin=ClaimOrigin.inferred,
                    recommended_action="Configure hospital HIS/EMR, PACS, LIS profile to run integration matrix.",
                    missing_evidence="Hospital infrastructure baseline",
                )
            )
        else:
            for idx, chk in enumerate(checks):
                status_raw = chk.get("status")
                sys_info = chk.get("hospital_system", {})
                sys_name = sys_info.get("name", "System")
                req_text = chk.get("requirement", "")
                vendor_cap = chk.get("vendor_capability", "")
                gap_desc = chk.get("gap_description") or ""

                if status_raw == CompatStatus.compatible:
                    f_status = FindingStatus.supported
                    sev = Severity.info
                    origin = ClaimOrigin.independently_verified
                elif status_raw == CompatStatus.partial:
                    f_status = FindingStatus.partially_supported
                    sev = Severity.medium
                    origin = ClaimOrigin.inferred
                elif status_raw == CompatStatus.incompatible:
                    f_status = FindingStatus.contradictory
                    sev = Severity.high
                    origin = ClaimOrigin.independently_verified
                else:
                    f_status = FindingStatus.insufficient_evidence
                    sev = Severity.medium
                    origin = ClaimOrigin.inferred

                finding_desc = f"{req_text}: {vendor_cap}."
                if gap_desc:
                    finding_desc += f" Gap: {gap_desc}"

                findings.append(
                    FindingItem(
                        id=uuid4(),
                        investigation_id=inv_id,
                        hospital_id=hosp_id,
                        agent=self.name,
                        dimension=self.dimension,
                        title=f"Integration Compatibility: {sys_name}",
                        description=finding_desc.strip(),
                        status=f_status,
                        severity=sev,
                        evidence_confidence=Confidence.medium,
                        claim_origin=origin,
                        recommended_action=chk.get("recommendation"),
                        missing_evidence="Interface specification or API documentation" if f_status != FindingStatus.supported else None,
                        evidence=[
                            FindingEvidenceRef(
                                source_name="Product Specifications & Architecture",
                                excerpt=f"Capability claim: {vendor_cap}",
                                is_independent=False,
                            )
                        ] if vendor_cap else [],
                    )
                )

        await self.emit_progress(inv_id, 100, "Integration compatibility analysis finished")
        return {"findings": findings, "evidence": evidence}
