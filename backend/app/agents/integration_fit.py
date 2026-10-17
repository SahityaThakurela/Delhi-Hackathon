"""Integration Fit Specialist Agent (BE-6).

Hands off to the Integration Compatibility Engine (services/integration_engine.py)
and converts compatibility evaluations into structured findings.
"""

from typing import Any, Dict, List
from uuid import uuid4

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import FindingItem, InvestigationState
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
        inv_id = state.get("investigation_id")
        hosp_id = state.get("hospital_id")

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
            for chk in checks:
                status_raw = chk.get("status")
                sys_info = chk.get("hospital_system", {})
                sys_name = sys_info.get("name", "System")

                if status_raw == CompatStatus.compatible:
                    f_status = FindingStatus.supported
                    sev = Severity.info
                elif status_raw == CompatStatus.partial:
                    f_status = FindingStatus.partially_supported
                    sev = Severity.medium
                elif status_raw == CompatStatus.incompatible:
                    f_status = FindingStatus.contradictory
                    sev = Severity.high
                else:
                    f_status = FindingStatus.insufficient_evidence
                    sev = Severity.medium

                findings.append(
                    FindingItem(
                        id=uuid4(),
                        investigation_id=inv_id,
                        hospital_id=hosp_id,
                        agent=self.name,
                        dimension=self.dimension,
                        title=f"Compatibility with {sys_name}",
                        description=f"{chk.get('requirement')}: {chk.get('vendor_capability')}. {chk.get('gap_description') or ''}".strip(),
                        status=f_status,
                        severity=sev,
                        evidence_confidence=Confidence.medium,
                        claim_origin=ClaimOrigin.independently_verified if f_status == FindingStatus.supported else ClaimOrigin.inferred,
                        recommended_action=chk.get("recommendation"),
                        missing_evidence="Interface engine documentation or API spec" if f_status != FindingStatus.supported else None,
                    )
                )

        return {"findings": findings, "evidence": evidence}
