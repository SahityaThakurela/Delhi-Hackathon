"""Integration Compatibility Engine and Blueprint Generator (P2 ownership).

Signature feature: evaluates hospital infrastructure compatibility and generates
actionable integration blueprints per BE-8 of Kyro Team Bible.
"""

from typing import Any, Dict, List
from uuid import uuid4

from backend.app.schemas.ai_schemas import (
    CompatStatus,
    Confidence,
    IntegrationCheckRow,
)
from backend.app.services.deterministic import standards_coverage


def evaluate_integration_compatibility(
    hospital_systems: List[Dict[str, Any]],
    vendor_product: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare vendor product capabilities against hospital infrastructure.

    Computes:
    - Matrix of checks (category, requirement, vendor_capability, status, gap, effort, recommendation)
    - Readiness score: 100 * (compatible + 0.5 * partial) / (all non-unknown rows)
    """
    checks: List[IntegrationCheckRow] = []
    claimed_standards = vendor_product.get("claimed_standards", [])

    for system in hospital_systems:
        category = system.get("category", "other")
        sys_name = system.get("name", "Unknown System")
        sys_standards = system.get("standards", [])

        cov = standards_coverage(sys_standards, claimed_standards)

        if cov["is_fully_covered"]:
            status = CompatStatus.compatible
            gap = None
            effort = "low"
            rec = f"Direct standard integration confirmed with {sys_name}."
        elif cov["matched"]:
            status = CompatStatus.partial
            gap = f"Missing support for standards: {', '.join(cov['missing'])}."
            effort = "medium"
            rec = f"Coordinate interface adapter or bridge for {sys_name}."
        else:
            status = CompatStatus.incompatible if cov["missing"] else CompatStatus.unknown
            gap = f"No shared protocol standards identified with {sys_name}."
            effort = "high"
            rec = f"Requires interface engine or custom API connector for {sys_name}."

        checks.append(
            IntegrationCheckRow(
                id=uuid4(),
                hospital_system={"category": category, "name": sys_name},
                requirement=f"Integration with {sys_name} ({category})",
                vendor_capability=f"Claims {', '.join(claimed_standards)}" if claimed_standards else "No standards claimed",
                status=status,
                gap_description=gap,
                effort=effort,
                recommendation=rec,
                evidence_ids=[],
                evidence_confidence=Confidence.medium,
            )
        )

    # Calculate readiness score
    evaluated_rows = [c for c in checks if c.status != CompatStatus.unknown]
    if evaluated_rows:
        comp_count = sum(1 for c in evaluated_rows if c.status == CompatStatus.compatible)
        partial_count = sum(1 for c in evaluated_rows if c.status == CompatStatus.partial)
        incompat_count = sum(1 for c in evaluated_rows if c.status == CompatStatus.incompatible)
        readiness_score = round(100.0 * (comp_count + 0.5 * partial_count) / len(evaluated_rows), 2)
    else:
        comp_count = partial_count = incompat_count = 0
        readiness_score = 0.0

    unknown_count = sum(1 for c in checks if c.status == CompatStatus.unknown)

    return {
        "summary": {
            "compatible": comp_count,
            "partial": partial_count,
            "incompatible": incompat_count,
            "unknown": unknown_count,
            "readiness_score": readiness_score,
        },
        "checks": [check.model_dump() for check in checks],
    }


def generate_blueprint(checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate structured integration phases with duration ranges and risk factors."""
    phases = [
        {
            "name": "Discovery & Architecture Validation",
            "duration_weeks": "2-3",
            "tasks": [
                "Audit network topology and firewall rules",
                "Review API specs and FHIR/HL7 schema mappings",
                "Confirm data residency and authentication mechanisms",
            ],
            "owner_role": "Hospital IT & Vendor Architect",
        },
        {
            "name": "Interface Build & Adapter Deployment",
            "duration_weeks": "3-5",
            "tasks": [
                "Deploy interface broker / adapter for protocol alignment",
                "Configure bidirectional endpoints and message queues",
                "Execute synthetic data ingestion and error routing tests",
            ],
            "owner_role": "Integration Engineer",
        },
        {
            "name": "Clinical Validation & UAT",
            "duration_weeks": "2-4",
            "tasks": [
                "Perform end-to-end user acceptance testing with hospital staff",
                "Validate consent workflows and audit trail persistence",
                "Sign-off clinical workflow compatibility",
            ],
            "owner_role": "Clinical Reviewer & Procurement Lead",
        },
        {
            "name": "Go-Live & Cutover",
            "duration_weeks": "1-2",
            "tasks": [
                "Execute parallel run monitoring",
                "Enable 24/7 telemetry and automated alerting watches",
                "Formal operational handover",
            ],
            "owner_role": "Hospital CIO & Vendor Lead",
        },
    ]

    risks = [
        "Unbudgeted interface engine licensing if vendor lacks native FHIR R4",
        "Legacy PACS DICOMweb upgrade delays",
        "Clinical workflow disruption during cutover window",
    ]

    return {
        "readiness_score": 75.0,
        "phases": phases,
        "risks": risks,
    }
