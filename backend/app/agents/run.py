"""Headless CLI runner for Kyro multi-agent investigation (BE-6).

Usage:
    python -m backend.app.agents.run --investigation-id <UUID>
"""

import argparse
import asyncio
from datetime import date, timedelta
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict
from uuid import UUID, uuid4

# Ensure project root is in sys.path for both 'backend.app' and 'app' runs
_agent_file = Path(__file__).resolve()
_root_dir = _agent_file.parent.parent.parent.parent
_backend_dir = _agent_file.parent.parent.parent
for _p in (str(_root_dir), str(_backend_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from backend.app.agents.orchestrator import build_investigation_graph
from backend.app.agents.state import InvestigationState
from backend.app.schemas.ai_schemas import Dimension, InvStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("kyro.agents.run")


def create_demo_state(investigation_id: UUID) -> InvestigationState:
    """Generate representative demonstration state with planted facts for headless testing."""
    hosp_id = uuid4()
    vendor_id = uuid4()
    product_id = uuid4()
    today = date.today()

    return {
        "investigation_id": investigation_id,
        "hospital_id": hosp_id,
        "title": "Headless Investigation Run",
        "hospital_profile": {
            "name": "Demo City Hospital",
            "city": "New Delhi",
            "state": "Delhi",
            "bed_count": 450,
            "abdm_maturity": 2,
            "risk_appetite": "conservative",
            "data_residency": "india_only",
        },
        "hospital_requirements": [
            {"dimension": "compliance", "title": "ABDM v3 API conformance", "mandatory": True, "rule": {"doc_type": "abdm_compliance"}},
            {"dimension": "security_privacy", "title": "ISO 27001 active certificate", "mandatory": True, "rule": {"type": "cert_valid"}},
            {"dimension": "security_privacy", "title": "Recent VAPT report", "mandatory": True, "rule": {"type": "report_recent"}},
            {"dimension": "security_privacy", "title": "India Data Residency", "mandatory": True, "rule": {"type": "residency_check"}},
        ],
        "hospital_systems": [
            {
                "category": "pacs",
                "name": "Orthanc PACS 1.12",
                "standards": ["DICOMweb", "HL7v2.5"],
            },
            {
                "category": "his_emr",
                "name": "LegacyHIS 4.2",
                "standards": ["HL7v2.5", "FHIR R4"],
            },
        ],
        "vendor": {
            "id": vendor_id,
            "name": "DemoSoft Technologies Ltd",
            "country": "India",
            "cin": "U72900DL2021PTC123456",
        },
        "product": {
            "id": product_id,
            "name": "DemoSoft HIS",
            "category": "his_emr",
            "version": "4.2.0",
            "description": "Comprehensive hospital management system with ABDM v3 claiming FHIR interoperability.",
            "claimed_standards": ["HL7v2.5", "FHIR 4.0.1", "ABDM v3"],
            "deployment_models": ["public_cloud"],
        },
        "documents": [
            {
                "id": uuid4(),
                "doc_type": "iso27001_cert",
                "filename": "ISO27001_cert_expired.pdf",
                "valid_until": (today - timedelta(days=90)).isoformat(),  # Planted expired cert
            },
            {
                "id": uuid4(),
                "doc_type": "vapt_report",
                "filename": "VAPT_audit_2024.pdf",
                "doc_date": (today - timedelta(days=450)).isoformat(),  # Planted stale VAPT (>365d)
            },
            {
                "id": uuid4(),
                "doc_type": "brochure",
                "filename": "Product_Brochure.pdf",
                # Brochure claim only for ABDM (should be unverified)
            },
        ],
        "selected_dimensions": list(Dimension),
        "instructions": "Focus on ABDM v3 and data residency in India.",
        "steering_commands": [],
        "status": InvStatus.draft,
        "agent_runs": {},
        "findings": [],
        "evidence": [],
        "debate_messages": [],
        "timeline_events": [],
        "dimension_scores": {},
        "overall_score": None,
        "score_confidence": None,
        "overall_risk": None,
        "summary": None,
        "errors": [],
    }


async def run_investigation(investigation_id: UUID) -> Dict[str, Any]:
    """Execute LangGraph multi-agent investigation workflow."""
    logger.info(f"Starting headless investigation: {investigation_id}")
    graph = build_investigation_graph()
    initial_state = create_demo_state(investigation_id)

    config = {"configurable": {"thread_id": str(investigation_id)}}
    final_state = await graph.ainvoke(initial_state, config=config)

    logger.info("Investigation workflow completed successfully!")
    logger.info(f"Final Status: {final_state.get('status')}")
    logger.info(f"Overall Trust Score: {final_state.get('overall_score')}/100")
    logger.info(f"Overall Risk: {final_state.get('overall_risk')}")
    logger.info(f"Total Findings Generated: {len(final_state.get('findings', []))}")
    logger.info(f"Total Debate Messages: {len(final_state.get('debate_messages', []))}")

    return final_state


def main():
    parser = argparse.ArgumentParser(description="Headless runner for Kyro multi-agent investigation.")
    parser.add_argument("--investigation-id", type=str, default=str(uuid4()), help="UUID of the investigation")
    args = parser.parse_args()

    inv_id = UUID(args.investigation_id)
    final_state = asyncio.run(run_investigation(inv_id))

    print("\n" + "=" * 60)
    print("KYRO INVESTIGATION SUMMARY")
    print("=" * 60)
    print(f"Summary: {final_state.get('summary')}")
    print("\nVerified Findings:")
    for f in final_state.get("findings", []):
        print(f"- [{f.severity.value.upper()}] ({f.status.value}) {f.title}: {f.description[:90]}...")
    print("\nSkeptic Debate History:")
    for d in final_state.get("debate_messages", []):
        print(f"  {d.role.value.upper()}: {d.content}")
    print("=" * 60)


if __name__ == "__main__":
    main()
