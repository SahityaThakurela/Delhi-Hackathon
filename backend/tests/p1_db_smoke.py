import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory, engine
from app.db.tenancy import scoped
from app.models import (
    Hospital,
    User,
    HospitalSystem,
    RequirementCatalogue,
    HospitalRequirement,
    Vendor,
    Product,
    Document,
    DocumentChunk,
    Investigation,
    AgentRun,
    SteeringCommand,
    TimelineEvent,
    Evidence,
    Finding,
    FindingEvidence,
    DebateMessage,
    DimensionScore,
    IntegrationCheck,
    IntegrationBlueprint,
    Report,
    Review,
    MonitoringWatch,
    Alert,
    AuditLog,
    UserRole,
    SystemCategory,
    DeploymentModel,
    RiskAppetite,
    Dimension,
    AgentName,
    FindingStatus,
    Severity,
    Confidence,
    ClaimOrigin,
    InvStatus,
    RunStatus,
    ReviewDecision,
    CompatStatus,
    EvidenceSource,
    DocStatus,
    ReportStatus,
    AlertStatus,
    DebateRole,
)


@pytest.mark.asyncio
async def test_p1_db_smoke_all_tables():
    """Performs one-row INSERT + SELECT for every table via the SQLAlchemy ORM."""
    async with async_session_factory() as session:
        # 1. Hospital
        hospital = Hospital(
            name="Apollo Smoke Hospital",
            city="Bengaluru",
            state="Karnataka",
            hospital_type="multi-specialty",
            bed_count=500,
            nabh_accredited=True,
            abdm_maturity=3,
            risk_appetite=RiskAppetite.balanced,
            annual_it_budget_inr=50000000,
            data_residency="india_only",
        )
        session.add(hospital)
        await session.flush()
        assert hospital.id is not None

        # Verify Hospital SELECT
        res = await session.execute(select(Hospital).where(Hospital.id == hospital.id))
        h_db = res.scalar_one()
        assert h_db.name == "Apollo Smoke Hospital"

        # 2. User
        user = User(
            hospital_id=hospital.id,
            email=f"admin_{uuid.uuid4().hex[:8]}@apollo.test",
            password_hash="$2b$12$e80M...hashed",
            full_name="Dr. Smoke Admin",
            role=UserRole.admin,
            is_active=True,
        )
        session.add(user)
        await session.flush()
        res = await session.execute(select(User).where(User.id == user.id))
        assert res.scalar_one().email == user.email

        # 3. Hospital System
        h_sys = HospitalSystem(
            hospital_id=hospital.id,
            category=SystemCategory.his_emr,
            name="SmokeHIS",
            vendor_name="DemoHIS Corp",
            version="4.2",
            standards=["HL7v2.5", "FHIR R4"],
            interfaces={"apis": ["REST"], "auth": ["OAuth2"]},
            deployment=DeploymentModel.on_prem,
            notes="Primary hospital HIS",
        )
        session.add(h_sys)
        await session.flush()
        res = await session.execute(select(HospitalSystem).where(HospitalSystem.id == h_sys.id))
        assert res.scalar_one().name == "SmokeHIS"

        # 4. Requirement Catalogue
        code_rand = f"SEC-SMOKE-{uuid.uuid4().hex[:6].upper()}"
        cat = RequirementCatalogue(
            code=code_rand,
            dimension=Dimension.security_privacy,
            title="ISO 27001 Certification Valid",
            description="Active ISO 27001 certification required",
            authority="ISO/IEC",
            reference_url="https://www.iso.org/isoiec-27001-information-security.html",
            reference_date=date(2022, 10, 1),
            applies_to={"product_categories": ["his_emr"]},
            check_type="deterministic",
            rule={"type": "cert_valid", "doc_type": "iso27001_cert"},
            default_severity=Severity.high,
        )
        session.add(cat)
        await session.flush()
        res = await session.execute(select(RequirementCatalogue).where(RequirementCatalogue.id == cat.id))
        assert res.scalar_one().code == code_rand

        # 5. Hospital Requirement
        h_req = HospitalRequirement(
            hospital_id=hospital.id,
            catalogue_id=cat.id,
            dimension=Dimension.security_privacy,
            title="Hospital ISO 27001 Requirement",
            description="Mandatory certificate validation",
            mandatory=True,
            severity_if_unmet=Severity.critical,
            rule={"type": "cert_valid"},
            is_custom=False,
        )
        session.add(h_req)
        await session.flush()
        res = await session.execute(select(HospitalRequirement).where(HospitalRequirement.id == h_req.id))
        assert res.scalar_one().title == "Hospital ISO 27001 Requirement"

        # 6. Vendor
        vendor = Vendor(
            hospital_id=hospital.id,
            name="SmokeSoft Technologies",
            website="https://smokesoft.example.in",
            country="India",
            cin="U72200DL2020PTC123456",
            contact_name="Rajesh Sharma",
            contact_email="rajesh@smokesoft.example.in",
            notes="HIS and LIS provider",
        )
        session.add(vendor)
        await session.flush()
        res = await session.execute(select(Vendor).where(Vendor.id == vendor.id))
        assert res.scalar_one().name == "SmokeSoft Technologies"

        # 7. Product
        product = Product(
            vendor_id=vendor.id,
            name="SmokeEMR Pro",
            category=SystemCategory.his_emr,
            version="v3.1",
            description="Integrated EMR suite",
            deployment_models=[DeploymentModel.saas, DeploymentModel.hybrid],
            claimed_standards=["FHIR R4", "ABDM M1"],
            claimed_certifications=["ISO 27001", "SOC 2 Type II"],
        )
        session.add(product)
        await session.flush()
        res = await session.execute(select(Product).where(Product.id == product.id))
        assert res.scalar_one().name == "SmokeEMR Pro"

        # 8. Document
        doc = Document(
            hospital_id=hospital.id,
            vendor_id=vendor.id,
            product_id=product.id,
            doc_type="iso27001_cert",
            filename="ISO_Cert_2025.pdf",
            storage_key=f"{hospital.id}/{vendor.id}/iso.pdf",
            mime_type="application/pdf",
            size_bytes=1048576,
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            version_label="2022-rev",
            doc_date=date(2023, 1, 15),
            valid_until=date(2026, 1, 14),
            status=DocStatus.processed,
            page_count=4,
            uploaded_by=user.id,
        )
        session.add(doc)
        await session.flush()
        res = await session.execute(select(Document).where(Document.id == doc.id))
        assert res.scalar_one().filename == "ISO_Cert_2025.pdf"

        # 9. Document Chunk (with pgvector embedding = 1536 floats)
        fake_embedding = [0.01 * (i % 10) for i in range(1536)]
        chunk = DocumentChunk(
            document_id=doc.id,
            hospital_id=hospital.id,
            chunk_index=0,
            page=1,
            content="This certificate certifies that SmokeSoft complies with ISO/IEC 27001:2022 standard.",
            token_count=18,
            embedding=fake_embedding,
        )
        session.add(chunk)
        await session.flush()
        res = await session.execute(select(DocumentChunk).where(DocumentChunk.id == chunk.id))
        chunk_db = res.scalar_one()
        assert chunk_db.token_count == 18
        assert len(chunk_db.embedding) == 1536

        # 10. Investigation
        inv = Investigation(
            hospital_id=hospital.id,
            vendor_id=vendor.id,
            product_id=product.id,
            created_by=user.id,
            title="Smoke Soft Evaluation 2026",
            status=InvStatus.running,
            dimensions=[Dimension.compliance, Dimension.security_privacy, Dimension.integration],
            instructions="Focus on ABDM compliance and ISO certificate validity",
            overall_score=Decimal("84.50"),
            score_confidence=Decimal("0.910"),
            overall_risk=Severity.low,
            summary="Initial review looks solid.",
            started_at=datetime.now(timezone.utc),
        )
        session.add(inv)
        await session.flush()
        res = await session.execute(select(Investigation).where(Investigation.id == inv.id))
        assert res.scalar_one().title == "Smoke Soft Evaluation 2026"

        # 11. Agent Run
        run = AgentRun(
            investigation_id=inv.id,
            agent=AgentName.compliance,
            status=RunStatus.running,
            progress=65,
            current_task="Analyzing ABDM M1 conformance documentation",
            output={"milestone": "checked"},
            token_usage={"prompt_tokens": 1200, "completion_tokens": 400},
            started_at=datetime.now(timezone.utc),
        )
        session.add(run)
        await session.flush()
        res = await session.execute(select(AgentRun).where(AgentRun.id == run.id))
        assert res.scalar_one().progress == 65

        # 12. Evidence
        ev = Evidence(
            hospital_id=hospital.id,
            investigation_id=inv.id,
            vendor_id=vendor.id,
            product_id=product.id,
            source_type=EvidenceSource.vendor_document,
            source_name="ISO_Cert_2025.pdf",
            source_url="https://smokesoft.example.in/certs/iso.pdf",
            document_id=doc.id,
            chunk_id=chunk.id,
            page=1,
            excerpt="Valid until 14 Jan 2026",
            doc_version="2022-rev",
            source_date=date(2023, 1, 15),
            is_independent=False,
            reliability=Confidence.high,
            content_hash="abc123hash",
        )
        session.add(ev)
        await session.flush()
        res = await session.execute(select(Evidence).where(Evidence.id == ev.id))
        assert res.scalar_one().excerpt == "Valid until 14 Jan 2026"

        # 13. Finding
        finding = Finding(
            investigation_id=inv.id,
            hospital_id=hospital.id,
            agent=AgentName.security_privacy,
            dimension=Dimension.security_privacy,
            requirement_id=h_req.id,
            title="ISO 27001 certificate verified active",
            description="Certificate validity extends through 2026.",
            status=FindingStatus.supported,
            severity=Severity.low,
            evidence_confidence=Confidence.high,
            claim_origin=ClaimOrigin.independently_verified,
            recommended_action="Track expiry in monitoring watch.",
            review_decision=ReviewDecision.pending,
        )
        session.add(finding)
        await session.flush()
        res = await session.execute(select(Finding).where(Finding.id == finding.id))
        assert res.scalar_one().title == "ISO 27001 certificate verified active"

        # 14. Finding Evidence (Link)
        fe = FindingEvidence(
            finding_id=finding.id,
            evidence_id=ev.id,
            relation="supports",
        )
        session.add(fe)
        await session.flush()
        res = await session.execute(
            select(FindingEvidence).where(
                FindingEvidence.finding_id == finding.id,
                FindingEvidence.evidence_id == ev.id,
            )
        )
        assert res.scalar_one().relation == "supports"

        # 15. Debate Message
        dm = DebateMessage(
            investigation_id=inv.id,
            finding_id=finding.id,
            seq=1,
            agent=AgentName.skeptic,
            role=DebateRole.challenge,
            content="Is the scope of ISO 27001 limited to headquarters or entire cloud infrastructure?",
            evidence_ids=[ev.id],
        )
        session.add(dm)
        await session.flush()
        res = await session.execute(select(DebateMessage).where(DebateMessage.id == dm.id))
        assert res.scalar_one().role == DebateRole.challenge

        # 16. Steering Command
        sc = SteeringCommand(
            investigation_id=inv.id,
            user_id=user.id,
            instruction="Deep-dive into ABDM v3 capabilities",
            parsed={"action": "focus", "subject": "abdm_v3"},
            status="applied",
        )
        session.add(sc)
        await session.flush()
        res = await session.execute(select(SteeringCommand).where(SteeringCommand.id == sc.id))
        assert res.scalar_one().status == "applied"

        # 17. Timeline Event
        te = TimelineEvent(
            investigation_id=inv.id,
            event="agent.completed",
            agent=AgentName.security_privacy,
            payload={"findings_count": 1},
        )
        session.add(te)
        await session.flush()
        res = await session.execute(select(TimelineEvent).where(TimelineEvent.id == te.id))
        assert res.scalar_one().event == "agent.completed"

        # 18. Dimension Score
        ds = DimensionScore(
            investigation_id=inv.id,
            dimension=Dimension.security_privacy,
            score=Decimal("88.00"),
            weight=Decimal("0.250"),
            confidence=Decimal("0.850"),
            rationale="Robust ISO certificate and no reported CVEs.",
        )
        session.add(ds)
        await session.flush()
        res = await session.execute(
            select(DimensionScore).where(
                DimensionScore.investigation_id == inv.id,
                DimensionScore.dimension == Dimension.security_privacy,
            )
        )
        assert res.scalar_one().score == Decimal("88.00")

        # 19. Integration Check
        ic = IntegrationCheck(
            investigation_id=inv.id,
            hospital_system_id=h_sys.id,
            requirement="FHIR R4 Patient resource read/write",
            vendor_capability="Supports FHIR R4 US Core + Indian ABDM extensions",
            status=CompatStatus.compatible,
            effort="low",
            recommendation="Direct API integration via OAuth2",
            evidence_ids=[ev.id],
            evidence_confidence=Confidence.high,
        )
        session.add(ic)
        await session.flush()
        res = await session.execute(select(IntegrationCheck).where(IntegrationCheck.id == ic.id))
        assert res.scalar_one().status == CompatStatus.compatible

        # 20. Integration Blueprint
        ib = IntegrationBlueprint(
            investigation_id=inv.id,
            readiness_score=Decimal("92.50"),
            phases={"phase1": "Discovery", "phase2": "Staging test"},
            risks={"downtime": "Minimal scheduled maintenance"},
        )
        session.add(ib)
        await session.flush()
        res = await session.execute(select(IntegrationBlueprint).where(IntegrationBlueprint.investigation_id == inv.id))
        assert res.scalar_one().readiness_score == Decimal("92.50")

        # 21. Report
        report = Report(
            investigation_id=inv.id,
            hospital_id=hospital.id,
            version=1,
            status=ReportStatus.draft,
            summary={"score": 84.5, "recommendation": "Proceed with pilot"},
            storage_key=f"{hospital.id}/{inv.id}/report_v1.pdf",
            generated_by=user.id,
        )
        session.add(report)
        await session.flush()
        res = await session.execute(select(Report).where(Report.id == report.id))
        assert res.scalar_one().version == 1

        # 22. Review
        review = Review(
            finding_id=finding.id,
            reviewer_id=user.id,
            decision=ReviewDecision.accepted,
            comment="Reviewed certificate independently; valid.",
        )
        session.add(review)
        await session.flush()
        res = await session.execute(select(Review).where(Review.id == review.id))
        assert res.scalar_one().decision == ReviewDecision.accepted

        # 23. Monitoring Watch
        mw = MonitoringWatch(
            hospital_id=hospital.id,
            vendor_id=vendor.id,
            product_id=product.id,
            watch_type="certificate_expiry",
            config={"days_before_notice": 60},
            active=True,
        )
        session.add(mw)
        await session.flush()
        res = await session.execute(select(MonitoringWatch).where(MonitoringWatch.id == mw.id))
        assert res.scalar_one().watch_type == "certificate_expiry"

        # 24. Alert
        alert = Alert(
            hospital_id=hospital.id,
            watch_id=mw.id,
            vendor_id=vendor.id,
            severity=Severity.medium,
            title="Certificate expiry reminder",
            detail="ISO 27001 certificate expires in 90 days",
            status=AlertStatus.new,
        )
        session.add(alert)
        await session.flush()
        res = await session.execute(select(Alert).where(Alert.id == alert.id))
        assert res.scalar_one().title == "Certificate expiry reminder"

        # 25. Audit Log
        audit = AuditLog(
            hospital_id=hospital.id,
            user_id=user.id,
            action="CREATE",
            entity_type="investigation",
            entity_id=inv.id,
            diff={"status": "running"},
            ip="192.168.1.100",
        )
        session.add(audit)
        await session.flush()
        res = await session.execute(select(AuditLog).where(AuditLog.id == audit.id))
        assert res.scalar_one().action == "CREATE"

        # Tenancy helper test: scoped()
        scoped_q = scoped(select(Vendor), Vendor, hospital.id)
        scoped_res = await session.execute(scoped_q)
        assert len(scoped_res.scalars().all()) >= 1

        # Rollback so smoke test does not pollute database
        await session.rollback()
