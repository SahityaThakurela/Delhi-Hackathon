"""Deterministic check service (P2 ownership).

Rule-based validators that produce structured results the agents turn into findings.
The LLM must not decide these. Pure Python functions per BE-5 of Kyro Team Bible.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from backend.app.schemas.ai_schemas import ClaimOrigin, FindingStatus, Severity


@dataclass
class DeterministicResult:
    """Structured result returned by deterministic validators."""
    status: FindingStatus
    severity_hint: Severity
    detail: str
    evidence_refs: List[UUID] = field(default_factory=list)
    origin: ClaimOrigin = ClaimOrigin.independently_verified


def cert_valid(document: Any, as_of_date: Optional[date] = None) -> DeterministicResult:
    """Validate certificate expiration date against as_of_date (defaults to today)."""
    check_date = as_of_date or date.today()
    valid_until = getattr(document, "valid_until", None)

    if not valid_until:
        return DeterministicResult(
            status=FindingStatus.insufficient_evidence,
            severity_hint=Severity.medium,
            detail="Document lacks valid_until date; validity cannot be verified deterministically.",
            origin=ClaimOrigin.inferred,
        )

    if isinstance(valid_until, datetime):
        valid_until = valid_until.date()

    if valid_until >= check_date:
        return DeterministicResult(
            status=FindingStatus.supported,
            severity_hint=Severity.info,
            detail=f"Certificate valid until {valid_until.isoformat()} (checked against {check_date.isoformat()}).",
            origin=ClaimOrigin.independently_verified,
        )
    else:
        return DeterministicResult(
            status=FindingStatus.contradictory,
            severity_hint=Severity.high,
            detail=f"Certificate expired on {valid_until.isoformat()} (checked against {check_date.isoformat()}).",
            origin=ClaimOrigin.independently_verified,
        )


def report_recent(document: Any, max_age_days: int = 365, as_of_date: Optional[date] = None) -> DeterministicResult:
    """Check whether a report (VAPT/Audit) was completed within max_age_days."""
    check_date = as_of_date or date.today()
    doc_date = getattr(document, "doc_date", None)

    if not doc_date:
        return DeterministicResult(
            status=FindingStatus.insufficient_evidence,
            severity_hint=Severity.medium,
            detail="Document lacks a recorded doc_date; recency cannot be determined.",
            origin=ClaimOrigin.inferred,
        )

    if isinstance(doc_date, datetime):
        doc_date = doc_date.date()

    age_days = (check_date - doc_date).days
    if age_days < 0:
        return DeterministicResult(
            status=FindingStatus.contradictory,
            severity_hint=Severity.medium,
            detail=f"Report date {doc_date.isoformat()} is in the future relative to {check_date.isoformat()}.",
            origin=ClaimOrigin.inferred,
        )

    if age_days <= max_age_days:
        return DeterministicResult(
            status=FindingStatus.supported,
            severity_hint=Severity.info,
            detail=f"Report dated {doc_date.isoformat()} is {age_days} days old (within {max_age_days} day limit).",
            origin=ClaimOrigin.independently_verified,
        )
    else:
        return DeterministicResult(
            status=FindingStatus.contradictory,
            severity_hint=Severity.high,
            detail=f"Report dated {doc_date.isoformat()} is {age_days} days old (exceeds {max_age_days} day limit).",
            origin=ClaimOrigin.independently_verified,
        )


def version_match(claimed_product_version: Optional[str], document_version_label: Optional[str]) -> DeterministicResult:
    """Check version alignment with semantic version awareness."""
    if not claimed_product_version or not document_version_label:
        return DeterministicResult(
            status=FindingStatus.insufficient_evidence,
            severity_hint=Severity.low,
            detail="Missing product version or document version label for comparison.",
            origin=ClaimOrigin.inferred,
        )

    clean_claimed = claimed_product_version.strip().lower().lstrip("v")
    clean_doc = document_version_label.strip().lower().lstrip("v")

    if clean_claimed == clean_doc:
        return DeterministicResult(
            status=FindingStatus.supported,
            severity_hint=Severity.info,
            detail=f"Version match confirmed ({claimed_product_version}).",
            origin=ClaimOrigin.independently_verified,
        )

    return DeterministicResult(
        status=FindingStatus.partially_supported,
        severity_hint=Severity.medium,
        detail=f"Version mismatch: Product claims '{claimed_product_version}' but document specifies '{document_version_label}'.",
        origin=ClaimOrigin.inferred,
    )


def normalize_standard_name(name: str) -> str:
    """Normalize standard names (e.g. 'FHIR 4.0.1' -> 'FHIR R4')."""
    cleaned = " ".join(name.strip().upper().split())
    cleaned = cleaned.replace("HL7 V", "HL7V").replace("HL7 ", "HL7V")
    if cleaned in ("FHIR 4.0.1", "FHIR 4.0", "FHIR R4B", "FHIR"):
        return "FHIR R4"
    return cleaned


def standards_coverage(hospital_standards: List[str], product_claimed_standards: List[str]) -> Dict[str, Any]:
    """Calculate matched and missing standards between hospital requirements and vendor claims."""
    norm_hospital = {normalize_standard_name(s): s for s in hospital_standards}
    norm_claimed = {normalize_standard_name(s) for s in product_claimed_standards}

    matched = [orig for norm, orig in norm_hospital.items() if norm in norm_claimed]
    missing = [orig for norm, orig in norm_hospital.items() if norm not in norm_claimed]

    return {
        "matched": matched,
        "missing": missing,
        "is_fully_covered": len(missing) == 0,
    }


def abdm_checks(product: Any, documents: List[Any]) -> DeterministicResult:
    """ABDM v3 API compliance is Supported ONLY if an ABDM compliance document exists."""
    abdm_docs = [
        d for d in documents
        if getattr(d, "doc_type", "") in ("abdm_compliance", "abdm_cert")
        or "abdm" in getattr(d, "filename", "").lower()
    ]
    if abdm_docs:
        return DeterministicResult(
            status=FindingStatus.supported,
            severity_hint=Severity.info,
            detail="ABDM compliance documentation found in vendor evidence files.",
            origin=ClaimOrigin.independently_verified,
        )

    claimed = getattr(product, "claimed_standards", []) or []
    claims_abdm = any("abdm" in s.lower() for s in claimed)

    if claims_abdm:
        return DeterministicResult(
            status=FindingStatus.unverified,
            severity_hint=Severity.high,
            detail="ABDM v3 compliance is claimed in vendor brochure/metadata, but no official compliance document/test report was provided.",
            origin=ClaimOrigin.vendor_claim,
        )

    return DeterministicResult(
        status=FindingStatus.insufficient_evidence,
        severity_hint=Severity.medium,
        detail="No ABDM compliance evidence or claims found for this product.",
        origin=ClaimOrigin.inferred,
    )


def residency_check(deployment_models: List[str], data_residency_policy: str = "india_only") -> DeterministicResult:
    """Verify deployment model compatibility with Indian data residency policy."""
    dep_set = {m.lower().strip() for m in deployment_models}

    if data_residency_policy == "india_only":
        if "public_cloud" in dep_set and not any(m in dep_set for m in ("on_prem", "private_cloud", "hybrid")):
            return DeterministicResult(
                status=FindingStatus.partially_supported,
                severity_hint=Severity.high,
                detail="Vendor uses public cloud without documented on-prem / private cloud options to enforce India data residency.",
                origin=ClaimOrigin.inferred,
            )

    return DeterministicResult(
        status=FindingStatus.supported,
        severity_hint=Severity.info,
        detail=f"Deployment models {deployment_models} satisfy residency policy '{data_residency_policy}'.",
        origin=ClaimOrigin.independently_verified,
    )


# Registry of rules keyed by rule.type field in requirement rows
RULES: Dict[str, Callable[..., DeterministicResult]] = {
    "cert_valid": cert_valid,
    "report_recent": report_recent,
    "version_match": version_match,
    "abdm_checks": abdm_checks,
    "residency_check": residency_check,
}
