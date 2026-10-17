"""Deterministic validation checks (P2 ownership).

Rule-based validators that produce structured results the agents turn into findings.
The LLM must not decide these. Pure Python functions per BE-5 of Kyro Team Bible.

Guiding Principles:
- Missing expiry dates must not imply validity.
- Expired certificates must be detected deterministically.
- Stale reports must be identified from actual document dates.
- Missing evidence is not automatically proof of non-compliance (insufficient_evidence).
- Normalise standard names before comparing them.
- A brochure alone cannot establish verified ABDM v3 compliance.
- Never infer residency guarantees without supporting evidence.
- Use the status enums specified by the team bible.
- Zero LLM calls.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
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
    extra: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, item: str) -> Any:
        """Allow dict-like subscripting for backward compatibility with existing tests/callers."""
        if hasattr(self, item):
            return getattr(self, item)
        if item in self.extra:
            return self.extra[item]
        raise KeyError(f"DeterministicResult has no key or field '{item}'")

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item) or item in self.extra

    def get(self, item: str, default: Any = None) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        return self.extra.get(item, default)


# ---------------------------------------------------------------------
# Internal Field Extraction & Date Normalization Helpers
# ---------------------------------------------------------------------

def _get_field(obj: Any, *field_names: str, default: Any = None) -> Any:
    """Retrieve the first non-None field from an object or dictionary."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        for name in field_names:
            if name in obj and obj[name] is not None:
                return obj[name]
        return default
    for name in field_names:
        val = getattr(obj, name, None)
        if val is not None:
            return val
    return default


def _parse_date(val: Any) -> Optional[date]:
    """Parse date from date, datetime, or ISO string."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        # Try ISO format
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(val.split("T")[0], "%Y-%m-%d").date()
            except ValueError:
                pass
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                pass
    return None


def _get_doc_id(document: Any) -> List[UUID]:
    """Safely extract UUID from document if present."""
    doc_id = _get_field(document, "id", "document_id")
    if doc_id:
        if isinstance(doc_id, UUID):
            return [doc_id]
        try:
            return [UUID(str(doc_id))]
        except (ValueError, TypeError):
            pass
    return []


# ---------------------------------------------------------------------
# 1. Certificate Validity Check
# ---------------------------------------------------------------------

def cert_valid(document: Any, as_of_date: Optional[Union[date, datetime, str]] = None) -> DeterministicResult:
    """Validate certificate expiration date against as_of_date.

    Rules:
    - Missing expiry date -> insufficient_evidence (never assume valid).
    - Expired certificate -> contradictory (severity: high).
    - Active certificate -> supported (severity: info).
    """
    check_date = _parse_date(as_of_date) or date.today()
    valid_until = _parse_date(_get_field(document, "valid_until", "expiration_date", "expiry_date"))
    evidence_refs = _get_doc_id(document)

    if not valid_until:
        return DeterministicResult(
            status=FindingStatus.insufficient_evidence,
            severity_hint=Severity.medium,
            detail="Certificate lacks an expiration date (valid_until); validity cannot be verified deterministically.",
            evidence_refs=evidence_refs,
            origin=ClaimOrigin.inferred,
        )

    if valid_until >= check_date:
        days_remaining = (valid_until - check_date).days
        return DeterministicResult(
            status=FindingStatus.supported,
            severity_hint=Severity.info,
            detail=f"Certificate is valid until {valid_until.isoformat()} ({days_remaining} days remaining as of {check_date.isoformat()}).",
            evidence_refs=evidence_refs,
            origin=ClaimOrigin.independently_verified,
            extra={"valid_until": valid_until, "days_remaining": days_remaining},
        )
    else:
        days_expired = (check_date - valid_until).days
        return DeterministicResult(
            status=FindingStatus.contradictory,
            severity_hint=Severity.high,
            detail=f"Certificate expired on {valid_until.isoformat()} ({days_expired} days ago relative to {check_date.isoformat()}).",
            evidence_refs=evidence_refs,
            origin=ClaimOrigin.independently_verified,
            extra={"valid_until": valid_until, "days_expired": days_expired},
        )


# ---------------------------------------------------------------------
# 2. Report Recency Check (VAPT / Audit)
# ---------------------------------------------------------------------

def report_recent(
    document: Any,
    max_age_days: int = 365,
    as_of_date: Optional[Union[date, datetime, str]] = None,
) -> DeterministicResult:
    """Check whether a security/audit report was completed within max_age_days.

    Rules:
    - Missing doc_date -> insufficient_evidence.
    - Future date -> contradictory.
    - Stale (age > max_age_days) -> contradictory (severity: high).
    - Recent (age <= max_age_days) -> supported (severity: info).
    """
    check_date = _parse_date(as_of_date) or date.today()
    doc_date = _parse_date(_get_field(document, "doc_date", "report_date", "date"))
    evidence_refs = _get_doc_id(document)

    if not doc_date:
        return DeterministicResult(
            status=FindingStatus.insufficient_evidence,
            severity_hint=Severity.medium,
            detail="Document lacks a recorded doc_date; recency cannot be determined.",
            evidence_refs=evidence_refs,
            origin=ClaimOrigin.inferred,
        )

    age_days = (check_date - doc_date).days

    if age_days < 0:
        return DeterministicResult(
            status=FindingStatus.contradictory,
            severity_hint=Severity.medium,
            detail=f"Report date {doc_date.isoformat()} is in the future relative to {check_date.isoformat()}.",
            evidence_refs=evidence_refs,
            origin=ClaimOrigin.inferred,
            extra={"age_days": age_days, "doc_date": doc_date},
        )

    if age_days <= max_age_days:
        return DeterministicResult(
            status=FindingStatus.supported,
            severity_hint=Severity.info,
            detail=f"Report dated {doc_date.isoformat()} is {age_days} days old (within {max_age_days} day limit).",
            evidence_refs=evidence_refs,
            origin=ClaimOrigin.independently_verified,
            extra={"age_days": age_days, "doc_date": doc_date},
        )
    else:
        return DeterministicResult(
            status=FindingStatus.contradictory,
            severity_hint=Severity.high,
            detail=f"Report dated {doc_date.isoformat()} is {age_days} days old (exceeds {max_age_days} day limit).",
            evidence_refs=evidence_refs,
            origin=ClaimOrigin.independently_verified,
            extra={"age_days": age_days, "doc_date": doc_date},
        )


# ---------------------------------------------------------------------
# 3. Semantic-Version Aware Version Matching
# ---------------------------------------------------------------------

def _parse_version_tuple(ver_str: str) -> Tuple[Optional[Tuple[int, ...]], str]:
    """Parse version string into integer tuple and non-numeric suffix."""
    clean = ver_str.strip().lower()
    for prefix in ("version", "ver", "v", "rel", "r"):
        if clean.startswith(prefix):
            clean = clean[len(prefix):].lstrip(" .-_")
            break

    # Extract leading numbers
    parts = re.split(r"[.\-_]", clean)
    num_parts = []
    suffix_parts = []
    has_seen_suffix = False

    for p in parts:
        if not has_seen_suffix and p.isdigit():
            num_parts.append(int(p))
        else:
            has_seen_suffix = True
            if p:
                suffix_parts.append(p)

    # Pad with zeros up to 3 components (e.g. 2.4 -> 2.4.0)
    while len(num_parts) < 3 and num_parts:
        num_parts.append(0)

    tup = tuple(num_parts) if num_parts else None
    suffix = "-".join(suffix_parts)
    return tup, suffix


def version_match(
    claimed_product_version: Optional[str],
    document_version_label: Optional[str],
) -> DeterministicResult:
    """Compare product version against document version label with semver awareness.

    Rules:
    - Missing version info -> insufficient_evidence.
    - Exact or normalized match -> supported.
    - Patch / minor revision drift -> partially_supported.
    - Major version mismatch -> contradictory.
    """
    if not claimed_product_version or not document_version_label:
        return DeterministicResult(
            status=FindingStatus.insufficient_evidence,
            severity_hint=Severity.low,
            detail="Missing product version or document version label for comparison.",
            origin=ClaimOrigin.inferred,
        )

    raw_claimed = str(claimed_product_version).strip()
    raw_doc = str(document_version_label).strip()

    tup_claimed, suf_claimed = _parse_version_tuple(raw_claimed)
    tup_doc, suf_doc = _parse_version_tuple(raw_doc)

    # If both could be parsed numerically
    if tup_claimed and tup_doc:
        if tup_claimed == tup_doc and suf_claimed == suf_doc:
            return DeterministicResult(
                status=FindingStatus.supported,
                severity_hint=Severity.info,
                detail=f"Version match confirmed ({raw_claimed} == {raw_doc}).",
                origin=ClaimOrigin.independently_verified,
            )

        # Check major version
        if tup_claimed[0] != tup_doc[0]:
            return DeterministicResult(
                status=FindingStatus.contradictory,
                severity_hint=Severity.high,
                detail=f"Major version mismatch: Product claims '{raw_claimed}' but evidence is for version '{raw_doc}'.",
                origin=ClaimOrigin.independently_verified,
            )

        # Minor or patch difference
        return DeterministicResult(
            status=FindingStatus.partially_supported,
            severity_hint=Severity.medium,
            detail=f"Version drift: Product claims '{raw_claimed}' while evidence specifies '{raw_doc}'.",
            origin=ClaimOrigin.inferred,
        )

    # Fallback to direct sanitized string comparison for non-numeric versions
    clean_c = re.sub(r"[^a-z0-9]", "", raw_claimed.lower())
    clean_d = re.sub(r"[^a-z0-9]", "", raw_doc.lower())

    if clean_c == clean_d:
        return DeterministicResult(
            status=FindingStatus.supported,
            severity_hint=Severity.info,
            detail=f"Version match confirmed ({raw_claimed}).",
            origin=ClaimOrigin.independently_verified,
        )

    return DeterministicResult(
        status=FindingStatus.partially_supported,
        severity_hint=Severity.medium,
        detail=f"Version discrepancy: Product claims '{raw_claimed}' but document specifies '{raw_doc}'.",
        origin=ClaimOrigin.inferred,
    )


# ---------------------------------------------------------------------
# 4. Standard Name Normalization & Standards Coverage
# ---------------------------------------------------------------------

def normalize_standard_name(name: str) -> str:
    """Normalize healthcare and security standard names for deterministic matching."""
    if not name:
        return ""
    cleaned = " ".join(str(name).strip().split())
    upper = cleaned.upper()

    # FHIR normalization
    if re.search(r"\bFHIR\b", upper):
        if any(v in upper for v in ("4.0.1", "4.0", "R4B", "R4", "V4")):
            return "FHIR R4"
        if any(v in upper for v in ("STU3", "3.0", "R3")):
            return "FHIR STU3"
        if any(v in upper for v in ("DSTU2", "2.0", "R2")):
            return "FHIR DSTU2"
        return "FHIR R4"

    # HL7 normalization
    if "HL7" in upper:
        if any(v in upper for v in ("2.5.1", "2.5", "V2.5")):
            return "HL7v2.5"
        if any(v in upper for v in ("2.3.1", "2.3", "V2.3")):
            return "HL7v2.3"
        if any(v in upper for v in ("2.4", "V2.4")):
            return "HL7v2.4"
        if any(v in upper for v in ("2.X", "V2", "2.")):
            return "HL7v2.x"
        if "V3" in upper or "3.0" in upper:
            return "HL7v3"
        return "HL7v2.5"

    # DICOM & DICOMweb
    if "DICOM" in upper or any(w in upper for w in ("WADO", "STOW", "QIDO")):
        if any(w in upper for w in ("WEB", "WADO", "STOW", "QIDO", "REST")):
            return "DICOMweb"
        return "DICOM"

    # ABDM
    if "ABDM" in upper or "ABHA" in upper or "NDHM" in upper:
        if "V3" in upper or "3.0" in upper or "M3" in upper:
            return "ABDM v3"
        return "ABDM v3"

    # ISO 27001
    if "27001" in upper:
        return "ISO 27001"

    # SNOMED & LOINC
    if "SNOMED" in upper:
        return "SNOMED CT"
    if "LOINC" in upper:
        return "LOINC"

    return cleaned


def standards_coverage(
    hospital_standards: Union[List[str], Any],
    product_claimed_standards: Union[List[str], Any],
) -> DeterministicResult:
    """Calculate matched and missing standards between hospital requirements and vendor claims.

    Returns a typed DeterministicResult that also supports dict subscripting
    (cov["matched"], cov["missing"], cov["is_fully_covered"]) for caller compatibility.
    """
    h_list = hospital_standards or []
    if hasattr(h_list, "standards"):
        h_list = getattr(h_list, "standards", [])
    if isinstance(h_list, str):
        h_list = [h_list]

    p_list = product_claimed_standards or []
    if hasattr(p_list, "claimed_standards"):
        p_list = getattr(p_list, "claimed_standards", [])
    if isinstance(p_list, str):
        p_list = [p_list]

    norm_hospital = {normalize_standard_name(s): s for s in h_list if s}
    norm_claimed = {normalize_standard_name(s) for s in p_list if s}

    matched = [orig for norm, orig in norm_hospital.items() if norm in norm_claimed]
    missing = [orig for norm, orig in norm_hospital.items() if norm not in norm_claimed]
    is_fully_covered = len(missing) == 0

    if not norm_hospital:
        status = FindingStatus.supported
        severity = Severity.info
        detail = "No specific standards required by hospital system."
    elif is_fully_covered:
        status = FindingStatus.supported
        severity = Severity.info
        detail = f"All required standards matched: {', '.join(matched)}."
    elif matched:
        status = FindingStatus.partially_supported
        severity = Severity.medium
        detail = f"Partial standards coverage. Matched: [{', '.join(matched)}]. Missing: [{', '.join(missing)}]."
    else:
        status = FindingStatus.contradictory if p_list else FindingStatus.insufficient_evidence
        severity = Severity.high
        detail = f"None of the required standards were matched. Missing: [{', '.join(missing)}]."

    extra = {
        "matched": matched,
        "missing": missing,
        "is_fully_covered": is_fully_covered,
    }

    return DeterministicResult(
        status=status,
        severity_hint=severity,
        detail=detail,
        origin=ClaimOrigin.independently_verified if is_fully_covered else ClaimOrigin.inferred,
        extra=extra,
    )


# ---------------------------------------------------------------------
# 5. Required Documents Checklist Validation
# ---------------------------------------------------------------------

def required_documents(vendor: Any, requirements: List[Any]) -> DeterministicResult:
    """Evaluate whether all required documentation types exist in the vendor's files.

    Feeds into missing evidence lists and investigation gaps.
    Missing evidence is not automatically proof of non-compliance (insufficient_evidence).
    """
    vendor_docs = _get_field(vendor, "documents", default=[]) or []
    present_types = set()
    evidence_refs = []

    for d in vendor_docs:
        dtype = _get_field(d, "doc_type", "type")
        if dtype:
            present_types.add(dtype.strip().lower())
        did = _get_doc_id(d)
        if did:
            evidence_refs.extend(did)

    missing_docs = []
    required_types = set()

    for req in requirements:
        rule = _get_field(req, "rule", default={})
        if isinstance(rule, dict):
            req_dtype = rule.get("doc_type") or rule.get("required_doc_type")
            if req_dtype:
                req_dtype_clean = req_dtype.strip().lower()
                required_types.add(req_dtype_clean)
                if req_dtype_clean not in present_types:
                    missing_docs.append(req_dtype_clean)

    missing_unique = sorted(list(set(missing_docs)))

    if not required_types:
        return DeterministicResult(
            status=FindingStatus.supported,
            severity_hint=Severity.info,
            detail="No mandatory document types required by active hospital checklist.",
            evidence_refs=evidence_refs,
            origin=ClaimOrigin.independently_verified,
            extra={"missing_doc_types": [], "present_doc_types": sorted(list(present_types))},
        )

    if not missing_unique:
        return DeterministicResult(
            status=FindingStatus.supported,
            severity_hint=Severity.info,
            detail=f"All {len(required_types)} required document types are present.",
            evidence_refs=evidence_refs,
            origin=ClaimOrigin.independently_verified,
            extra={"missing_doc_types": [], "present_doc_types": sorted(list(present_types))},
        )

    return DeterministicResult(
        status=FindingStatus.insufficient_evidence,
        severity_hint=Severity.high,
        detail=f"Missing required documentation: {', '.join(missing_unique)}.",
        evidence_refs=evidence_refs,
        origin=ClaimOrigin.inferred,
        extra={"missing_doc_types": missing_unique, "present_doc_types": sorted(list(present_types))},
    )


# ---------------------------------------------------------------------
# 6. ABDM v3 Compliance Check
# ---------------------------------------------------------------------

def abdm_checks(product: Any, documents: Optional[List[Any]] = None) -> DeterministicResult:
    """ABDM v3 API compliance verification.

    Rules:
    - Supported ONLY if an ABDM compliance document / official test report exists.
    - Vendor brochure or marketing claim alone = unverified (vendor_claim).
    - No claims and no evidence = insufficient_evidence.
    """
    doc_list = documents if documents is not None else _get_field(product, "documents", default=[])
    doc_list = doc_list or []

    abdm_docs = []
    for d in doc_list:
        dtype = str(_get_field(d, "doc_type", "")).lower()
        fname = str(_get_field(d, "filename", "")).lower()
        if dtype in ("abdm_compliance", "abdm_cert", "ndhm_compliance", "abdm_report") or "abdm" in fname:
            abdm_docs.append(d)

    if abdm_docs:
        refs = []
        for d in abdm_docs:
            refs.extend(_get_doc_id(d))
        return DeterministicResult(
            status=FindingStatus.supported,
            severity_hint=Severity.info,
            detail="ABDM v3 compliance certified with official test report/certificate on file.",
            evidence_refs=refs,
            origin=ClaimOrigin.independently_verified,
        )

    claimed_standards = _get_field(product, "claimed_standards", default=[]) or []
    claimed_certs = _get_field(product, "claimed_certifications", default=[]) or []
    desc = str(_get_field(product, "description", "")).lower()

    all_claims = [str(s).lower() for s in claimed_standards + claimed_certs]
    claims_abdm = any("abdm" in s or "abha" in s for s in all_claims) or ("abdm" in desc and "v3" in desc)

    if claims_abdm:
        return DeterministicResult(
            status=FindingStatus.unverified,
            severity_hint=Severity.high,
            detail="ABDM v3 compliance is claimed in vendor metadata/brochure, but no official test report or sandbox certification was provided.",
            origin=ClaimOrigin.vendor_claim,
        )

    return DeterministicResult(
        status=FindingStatus.insufficient_evidence,
        severity_hint=Severity.medium,
        detail="No ABDM compliance evidence or claims found for this product.",
        origin=ClaimOrigin.inferred,
    )


# ---------------------------------------------------------------------
# 7. Data Residency Policy Check
# ---------------------------------------------------------------------

def residency_check(
    deployment_models: Union[List[str], Any],
    data_residency_policy: str = "india_only",
    documents: Optional[List[Any]] = None,
) -> DeterministicResult:
    """Verify deployment model and architecture compliance with India data residency policy.

    Rules:
    - Never infer residency guarantees without supporting evidence.
    - If deployment_models is empty -> insufficient_evidence.
    - Public cloud without India region proof or local deployment -> partially_supported (severity: high).
    - On-premises, private cloud, or verified India-region cloud -> supported.
    """
    dep_list = deployment_models or []
    if hasattr(dep_list, "deployment_models"):
        dep_list = getattr(dep_list, "deployment_models", [])
    if isinstance(dep_list, str):
        dep_list = [dep_list]

    if not dep_list:
        return DeterministicResult(
            status=FindingStatus.insufficient_evidence,
            severity_hint=Severity.high,
            detail="No deployment models specified; data residency compliance cannot be evaluated.",
            origin=ClaimOrigin.inferred,
        )

    dep_set = {str(m).lower().strip() for m in dep_list}

    if data_residency_policy == "india_only":
        # Check if vendor provided explicit data residency policy doc
        residency_docs = []
        if documents:
            for d in documents:
                dtype = str(_get_field(d, "doc_type", "")).lower()
                fname = str(_get_field(d, "filename", "")).lower()
                if "residency" in dtype or "residency" in fname or "dpdp" in dtype:
                    residency_docs.append(d)

        # On-prem or private cloud deployed locally guarantees India residency
        if any(m in dep_set for m in ("on_prem", "private_cloud")):
            return DeterministicResult(
                status=FindingStatus.supported,
                severity_hint=Severity.info,
                detail=f"Deployment models {list(dep_set)} satisfy India data residency policy via local infrastructure control.",
                origin=ClaimOrigin.independently_verified,
            )

        # Public cloud / SaaS requires explicit India data center documentation
        if any(m in dep_set for m in ("public_cloud", "saas", "hybrid")):
            if residency_docs:
                refs = []
                for d in residency_docs:
                    refs.extend(_get_doc_id(d))
                return DeterministicResult(
                    status=FindingStatus.supported,
                    severity_hint=Severity.info,
                    detail="Cloud deployment supported by verified India data residency documentation.",
                    evidence_refs=refs,
                    origin=ClaimOrigin.independently_verified,
                )

            return DeterministicResult(
                status=FindingStatus.partially_supported,
                severity_hint=Severity.high,
                detail=f"Vendor claims cloud deployment {list(dep_set)} without verified documentation confirming in-country (India) data storage and processing.",
                origin=ClaimOrigin.inferred,
            )

    return DeterministicResult(
        status=FindingStatus.supported,
        severity_hint=Severity.info,
        detail=f"Deployment models {list(dep_set)} satisfy residency policy '{data_residency_policy}'.",
        origin=ClaimOrigin.independently_verified,
    )


# ---------------------------------------------------------------------
# 8. Rules Registry Keyed by rule.type
# ---------------------------------------------------------------------

RULES: Dict[str, Callable[..., DeterministicResult]] = {
    "cert_valid": cert_valid,
    "report_recent": report_recent,
    "version_match": version_match,
    "required_documents": required_documents,
    "standards_coverage": standards_coverage,
    "abdm_checks": abdm_checks,
    "residency_check": residency_check,
}
