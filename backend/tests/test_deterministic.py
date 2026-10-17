"""Comprehensive unit tests for deterministic checks (BE-5).

Covers:
- Boundary dates (same day, expired yesterday, expires tomorrow)
- Leap years (Feb 29)
- Missing, empty, and malformed metadata
- Version matching & semantic comparison
- Standard name normalization & coverage
- Document requirement gaps
- ABDM v3 evidence vs claim verification
- India data residency checks
- RULES registry mapping
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.schemas.ai_schemas import ClaimOrigin, FindingStatus, Severity
from backend.app.services.deterministic import (
    RULES,
    DeterministicResult,
    abdm_checks,
    cert_valid,
    normalize_standard_name,
    report_recent,
    required_documents,
    residency_check,
    standards_coverage,
    version_match,
)


class MockDoc:
    """Helper mock document object."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# =====================================================================
# 1. Certificate Validity Tests (Boundary dates, leap years, missing data)
# =====================================================================

def test_cert_valid_active():
    """Future expiration date returns supported with info severity."""
    doc = MockDoc(valid_until=date(2027, 12, 31), id=uuid4())
    res = cert_valid(doc, as_of_date=date(2026, 10, 17))
    assert res.status == FindingStatus.supported
    assert res.severity_hint == Severity.info
    assert res.origin == ClaimOrigin.independently_verified
    assert doc.id in res.evidence_refs


def test_cert_valid_expired():
    """Past expiration date returns contradictory with high severity."""
    doc = MockDoc(valid_until=date(2025, 3, 31), id=uuid4())
    res = cert_valid(doc, as_of_date=date(2026, 10, 17))
    assert res.status == FindingStatus.contradictory
    assert res.severity_hint == Severity.high
    assert res.origin == ClaimOrigin.independently_verified
    assert doc.id in res.evidence_refs


def test_cert_valid_boundary_same_day():
    """Certificate valid through today is supported."""
    today = date(2026, 10, 17)
    doc = MockDoc(valid_until=today)
    res = cert_valid(doc, as_of_date=today)
    assert res.status == FindingStatus.supported
    assert res.severity_hint == Severity.info


def test_cert_valid_boundary_expired_yesterday():
    """Certificate that expired yesterday is contradictory."""
    today = date(2026, 10, 17)
    yesterday = today - timedelta(days=1)
    doc = MockDoc(valid_until=yesterday)
    res = cert_valid(doc, as_of_date=today)
    assert res.status == FindingStatus.contradictory
    assert res.severity_hint == Severity.high


def test_cert_valid_boundary_expires_tomorrow():
    """Certificate that expires tomorrow is supported."""
    today = date(2026, 10, 17)
    tomorrow = today + timedelta(days=1)
    doc = MockDoc(valid_until=tomorrow)
    res = cert_valid(doc, as_of_date=today)
    assert res.status == FindingStatus.supported


def test_cert_valid_leap_year():
    """Handles leap year Feb 29 date accurately."""
    doc = MockDoc(valid_until=date(2024, 2, 29))
    # On Feb 28, 2024 it is valid
    res_before = cert_valid(doc, as_of_date=date(2024, 2, 28))
    assert res_before.status == FindingStatus.supported

    # On Mar 1, 2024 it is expired
    res_after = cert_valid(doc, as_of_date=date(2024, 3, 1))
    assert res_after.status == FindingStatus.contradictory


def test_cert_valid_missing_date():
    """Missing valid_until returns insufficient_evidence (never assumes validity)."""
    doc = MockDoc(valid_until=None)
    res = cert_valid(doc, as_of_date=date(2026, 10, 17))
    assert res.status == FindingStatus.insufficient_evidence
    assert res.severity_hint == Severity.medium


def test_cert_valid_empty_string_date():
    """Empty string valid_until returns insufficient_evidence."""
    doc = {"valid_until": "   "}
    res = cert_valid(doc, as_of_date=date(2026, 10, 17))
    assert res.status == FindingStatus.insufficient_evidence


def test_cert_valid_malformed_string_date():
    """Malformed date string returns insufficient_evidence."""
    doc = {"valid_until": "not-a-real-date"}
    res = cert_valid(doc, as_of_date=date(2026, 10, 17))
    assert res.status == FindingStatus.insufficient_evidence


def test_cert_valid_datetime_input():
    """Supports datetime instances and normalizes to date."""
    dt = datetime(2027, 5, 20, 14, 30, 0)
    doc = MockDoc(valid_until=dt)
    res = cert_valid(doc, as_of_date=date(2026, 10, 17))
    assert res.status == FindingStatus.supported


def test_cert_valid_iso_string_input():
    """Parses ISO formatted date string correctly."""
    doc = {"valid_until": "2027-01-15T00:00:00Z"}
    res = cert_valid(doc, as_of_date=date(2026, 10, 17))
    assert res.status == FindingStatus.supported


# =====================================================================
# 2. Report Recency Tests (VAPT, audits, age thresholds)
# =====================================================================

def test_report_recent_fresh():
    """Report from 30 days ago is supported."""
    today = date(2026, 10, 17)
    doc = MockDoc(doc_date=today - timedelta(days=30), id=uuid4())
    res = report_recent(doc, max_age_days=365, as_of_date=today)
    assert res.status == FindingStatus.supported
    assert res.severity_hint == Severity.info
    assert doc.id in res.evidence_refs


def test_report_recent_stale():
    """Report older than 365 days is contradictory with high severity."""
    today = date(2026, 10, 17)
    doc = MockDoc(doc_date=today - timedelta(days=400), id=uuid4())
    res = report_recent(doc, max_age_days=365, as_of_date=today)
    assert res.status == FindingStatus.contradictory
    assert res.severity_hint == Severity.high


def test_report_recent_boundary_exact_365():
    """Report exactly 365 days old is supported."""
    today = date(2026, 10, 17)
    doc = MockDoc(doc_date=today - timedelta(days=365))
    res = report_recent(doc, max_age_days=365, as_of_date=today)
    assert res.status == FindingStatus.supported


def test_report_recent_boundary_366_days():
    """Report 366 days old exceeds threshold and is contradictory."""
    today = date(2026, 10, 17)
    doc = MockDoc(doc_date=today - timedelta(days=366))
    res = report_recent(doc, max_age_days=365, as_of_date=today)
    assert res.status == FindingStatus.contradictory
    assert res.severity_hint == Severity.high


def test_report_recent_custom_max_age():
    """Custom max_age_days (e.g. 180 days for financial reviews) works."""
    today = date(2026, 10, 17)
    doc = MockDoc(doc_date=today - timedelta(days=200))
    res = report_recent(doc, max_age_days=180, as_of_date=today)
    assert res.status == FindingStatus.contradictory


def test_report_recent_future_date():
    """Future date report is flagged as contradictory."""
    today = date(2026, 10, 17)
    doc = MockDoc(doc_date=today + timedelta(days=5))
    res = report_recent(doc, as_of_date=today)
    assert res.status == FindingStatus.contradictory


def test_report_recent_missing_date():
    """Missing doc_date returns insufficient_evidence."""
    doc = MockDoc(doc_date=None)
    res = report_recent(doc, as_of_date=date(2026, 10, 17))
    assert res.status == FindingStatus.insufficient_evidence


# =====================================================================
# 3. Version Matching Tests (Semantic version comparison)
# =====================================================================

def test_version_match_exact():
    """Exact identical versions return supported."""
    res = version_match("4.2.0", "4.2.0")
    assert res.status == FindingStatus.supported
    assert res.severity_hint == Severity.info


def test_version_match_v_prefix():
    """Normalizes 'v' prefix."""
    res = version_match("v2.4", "2.4")
    assert res.status == FindingStatus.supported


def test_version_match_semantic_zero_extension():
    """Semantic comparison matches '2.4' with '2.4.0'."""
    res = version_match("2.4", "2.4.0")
    assert res.status == FindingStatus.supported


def test_version_match_patch_difference():
    """Minor / patch drift returns partially_supported."""
    res = version_match("4.2", "4.2.3")
    assert res.status == FindingStatus.partially_supported
    assert res.severity_hint == Severity.medium


def test_version_match_major_mismatch():
    """Major version mismatch returns contradictory."""
    res = version_match("3.1", "4.0")
    assert res.status == FindingStatus.contradictory
    assert res.severity_hint == Severity.high


def test_version_match_malformed_string():
    """Malformed non-numeric version strings compared gracefully."""
    res = version_match("release_alpha", "release_beta")
    assert res.status == FindingStatus.partially_supported


def test_version_match_missing():
    """Missing version arguments return insufficient_evidence."""
    res = version_match(None, "4.2")
    assert res.status == FindingStatus.insufficient_evidence

    res_empty = version_match("4.2", "")
    assert res_empty.status == FindingStatus.insufficient_evidence


# =====================================================================
# 4. Standard Name Normalization & Standards Coverage Tests
# =====================================================================

def test_normalize_standard_fhir():
    """Normalizes FHIR variations to canonical standards."""
    assert normalize_standard_name("FHIR 4.0.1") == "FHIR R4"
    assert normalize_standard_name("fhir r4") == "FHIR R4"
    assert normalize_standard_name("FHIR STU3") == "FHIR STU3"
    assert normalize_standard_name("FHIR DSTU2") == "FHIR DSTU2"


def test_normalize_standard_hl7():
    """Normalizes HL7 variations."""
    assert normalize_standard_name("hl7 v2.5") == "HL7v2.5"
    assert normalize_standard_name("HL7 2.5.1") == "HL7v2.5"
    assert normalize_standard_name("HL7 v2.3") == "HL7v2.3"
    assert normalize_standard_name("HL7 2.4") == "HL7v2.4"


def test_normalize_standard_dicom():
    """Normalizes DICOM and DICOMweb variations."""
    assert normalize_standard_name("DICOM") == "DICOM"
    assert normalize_standard_name("dicomweb") == "DICOMweb"
    assert normalize_standard_name("WADO-RS") == "DICOMweb"
    assert normalize_standard_name("STOW-RS") == "DICOMweb"


def test_normalize_standard_abdm_iso():
    """Normalizes ABDM and ISO standards."""
    assert normalize_standard_name("ABDM v3.0") == "ABDM v3"
    assert normalize_standard_name("ISO27001") == "ISO 27001"
    assert normalize_standard_name("ISO 27001:2022") == "ISO 27001"


def test_standards_coverage_full():
    """All required standards matched."""
    hospital = ["FHIR R4", "HL7v2.5"]
    vendor = ["FHIR 4.0.1", "HL7 2.5", "DICOM"]
    res = standards_coverage(hospital, vendor)
    assert res.status == FindingStatus.supported
    assert res["is_fully_covered"] is True
    assert len(res["missing"]) == 0


def test_standards_coverage_partial():
    """Partial coverage yields partially_supported."""
    hospital = ["FHIR R4", "HL7v2.5", "DICOMweb"]
    vendor = ["FHIR 4.0.1", "HL7 2.5"]
    res = standards_coverage(hospital, vendor)
    assert res.status == FindingStatus.partially_supported
    assert res.severity_hint == Severity.medium
    assert "DICOMweb" in res["missing"]
    assert res["is_fully_covered"] is False


def test_standards_coverage_none():
    """Zero matched standards yields contradictory."""
    hospital = ["DICOMweb", "ABDM v3"]
    vendor = ["HL7v2.3"]
    res = standards_coverage(hospital, vendor)
    assert res.status == FindingStatus.contradictory
    assert res.severity_hint == Severity.high
    assert res["is_fully_covered"] is False


def test_standards_coverage_empty_hospital():
    """No hospital standards required returns supported."""
    res = standards_coverage([], ["FHIR R4"])
    assert res.status == FindingStatus.supported
    assert res["is_fully_covered"] is True


# =====================================================================
# 5. Required Documents Checklist Tests
# =====================================================================

def test_required_documents_all_present():
    """All required document types exist in vendor documents."""
    vendor = {
        "documents": [
            {"doc_type": "iso27001_cert", "id": uuid4()},
            {"doc_type": "vapt_report", "id": uuid4()},
            {"doc_type": "abdm_compliance", "id": uuid4()},
        ]
    }
    requirements = [
        {"rule": {"doc_type": "iso27001_cert"}},
        {"rule": {"doc_type": "vapt_report"}},
    ]
    res = required_documents(vendor, requirements)
    assert res.status == FindingStatus.supported
    assert res.severity_hint == Severity.info
    assert len(res["missing_doc_types"]) == 0


def test_required_documents_missing():
    """Missing document types returns insufficient_evidence with list."""
    vendor = {
        "documents": [
            {"doc_type": "iso27001_cert", "id": uuid4()},
        ]
    }
    requirements = [
        {"rule": {"doc_type": "iso27001_cert"}},
        {"rule": {"doc_type": "vapt_report"}},
        {"rule": {"doc_type": "dpdp_policy"}},
    ]
    res = required_documents(vendor, requirements)
    assert res.status == FindingStatus.insufficient_evidence
    assert res.severity_hint == Severity.high
    assert "vapt_report" in res["missing_doc_types"]
    assert "dpdp_policy" in res["missing_doc_types"]


def test_required_documents_empty_vendor():
    """Vendor with no documents returns insufficient_evidence."""
    vendor = {"documents": []}
    requirements = [{"rule": {"doc_type": "iso27001_cert"}}]
    res = required_documents(vendor, requirements)
    assert res.status == FindingStatus.insufficient_evidence


# =====================================================================
# 6. ABDM v3 Compliance Tests
# =====================================================================

def test_abdm_checks_verified_with_document():
    """Supported ONLY when an official ABDM compliance document exists."""
    doc_id = uuid4()
    docs = [MockDoc(doc_type="abdm_compliance", id=doc_id)]
    product = MockDoc(claimed_standards=["ABDM v3"])
    res = abdm_checks(product, docs)
    assert res.status == FindingStatus.supported
    assert res.severity_hint == Severity.info
    assert res.origin == ClaimOrigin.independently_verified
    assert doc_id in res.evidence_refs


def test_abdm_checks_brochure_claim_only():
    """Vendor brochure or standards claim alone returns unverified (vendor_claim)."""
    docs = [MockDoc(doc_type="brochure", filename="product_brochure.pdf")]
    product = MockDoc(claimed_standards=["ABDM v3", "FHIR R4"])
    res = abdm_checks(product, docs)
    assert res.status == FindingStatus.unverified
    assert res.severity_hint == Severity.high
    assert res.origin == ClaimOrigin.vendor_claim


def test_abdm_checks_missing_entirely():
    """No ABDM claim and no document returns insufficient_evidence."""
    docs = [MockDoc(doc_type="iso27001_cert")]
    product = MockDoc(claimed_standards=["HL7v2.5"])
    res = abdm_checks(product, docs)
    assert res.status == FindingStatus.insufficient_evidence


# =====================================================================
# 7. Data Residency Tests
# =====================================================================

def test_residency_check_on_prem():
    """On-premises deployment satisfies India data residency."""
    res = residency_check(["on_prem"], "india_only")
    assert res.status == FindingStatus.supported
    assert res.severity_hint == Severity.info


def test_residency_check_private_cloud():
    """Private cloud deployment satisfies India data residency."""
    res = residency_check(["private_cloud"], "india_only")
    assert res.status == FindingStatus.supported


def test_residency_check_public_cloud_warning():
    """Public cloud without residency documentation yields partially_supported."""
    res = residency_check(["public_cloud"], "india_only")
    assert res.status == FindingStatus.partially_supported
    assert res.severity_hint == Severity.high


def test_residency_check_public_cloud_with_proof():
    """Public cloud with India data center document is supported."""
    doc_id = uuid4()
    docs = [MockDoc(doc_type="dpdp_residency_policy", id=doc_id)]
    res = residency_check(["public_cloud"], "india_only", documents=docs)
    assert res.status == FindingStatus.supported
    assert doc_id in res.evidence_refs


def test_residency_check_empty_models():
    """Empty deployment models returns insufficient_evidence."""
    res = residency_check([], "india_only")
    assert res.status == FindingStatus.insufficient_evidence
    assert res.severity_hint == Severity.high


# =====================================================================
# 8. Rules Registry Tests
# =====================================================================

def test_rules_registry():
    """Verify RULES registry maps all rule types to callable functions."""
    expected_rules = [
        "cert_valid",
        "report_recent",
        "version_match",
        "required_documents",
        "standards_coverage",
        "abdm_checks",
        "residency_check",
    ]
    for rule_name in expected_rules:
        assert rule_name in RULES
        assert callable(RULES[rule_name])
