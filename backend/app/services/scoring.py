"""Trust score engine (P2 ownership).

Deterministic trust scoring implementing the exact formula in Section 11.1 of docs/KYRO_TEAM_BIBLE.pdf.
Zero LLM hallucination: computed purely from findings and hospital requirements.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from backend.app.schemas.ai_schemas import (
    Confidence,
    Dimension,
    DimensionScore,
    FindingStatus,
    Severity,
    TrustScoreResponse,
)

# ---------------------------------------------------------------------
# Weights and Factors (Section 11.1)
# ---------------------------------------------------------------------

SEVERITY_WEIGHTS: Dict[Severity, float] = {
    Severity.critical: 30.0,
    Severity.high: 15.0,
    Severity.medium: 7.0,
    Severity.low: 3.0,
    Severity.info: 0.0,
}

STATUS_FACTORS: Dict[FindingStatus, Optional[float]] = {
    FindingStatus.contradictory: 1.0,
    FindingStatus.unverified: 0.5,
    FindingStatus.partially_supported: 0.5,
    FindingStatus.insufficient_evidence: 0.4,
    FindingStatus.supported: 0.0,
    FindingStatus.not_applicable: None,  # excluded
}

CONFIDENCE_WEIGHTS: Dict[Confidence, float] = {
    Confidence.high: 1.0,
    Confidence.medium: 0.6,
    Confidence.low: 0.3,
}

DEFAULT_DIMENSION_WEIGHTS: Dict[Dimension, float] = {
    Dimension.compliance: 0.25,
    Dimension.security_privacy: 0.25,
    Dimension.integration: 0.20,
    Dimension.clinical: 0.10,
    Dimension.financial: 0.10,
    Dimension.operations: 0.10,
}


def compute_dimension_score(findings: List[Any], dimension: Dimension) -> Dict[str, Any]:
    """Compute score and confidence for a specific dimension."""
    dim_findings = [
        f for f in findings
        if (getattr(f, "dimension", None) == dimension or getattr(f, "dimension", None) == dimension.value)
    ]

    applicable_findings = [
        f for f in dim_findings
        if getattr(f, "status", None) not in (FindingStatus.not_applicable, FindingStatus.not_applicable.value)
    ]

    if not applicable_findings and any(
        getattr(f, "status", None) in (FindingStatus.not_applicable, FindingStatus.not_applicable.value)
        for f in dim_findings
    ):
        return {
            "applicable": False,
            "score": 100.0,
            "confidence": 0.0,
            "penalties": 0.0,
            "finding_count": len(dim_findings),
        }

    total_penalty = 0.0
    weighted_conf_sum = 0.0
    severity_weight_sum = 0.0

    for f in applicable_findings:
        sev = getattr(f, "severity", Severity.medium)
        if isinstance(sev, str):
            sev = Severity(sev)

        status = getattr(f, "status", FindingStatus.unverified)
        if isinstance(status, str):
            status = FindingStatus(status)

        conf = getattr(f, "evidence_confidence", Confidence.medium)
        if isinstance(conf, str):
            conf = Confidence(conf)

        is_mandatory = getattr(f, "is_mandatory", True)
        mand_factor = 1.0 if is_mandatory else 0.6

        sev_weight = SEVERITY_WEIGHTS.get(sev, 7.0)
        stat_factor = STATUS_FACTORS.get(status, 0.5)

        if stat_factor is not None:
            penalty = sev_weight * stat_factor * mand_factor
            total_penalty += penalty

        conf_weight = CONFIDENCE_WEIGHTS.get(conf, 0.6)
        weighted_conf_sum += conf_weight * sev_weight
        severity_weight_sum += sev_weight

    score = max(0.0, 100.0 - total_penalty)
    confidence = (weighted_conf_sum / severity_weight_sum) if severity_weight_sum > 0 else 0.0

    return {
        "applicable": True,
        "score": round(score, 2),
        "confidence": round(confidence, 3),
        "penalties": round(total_penalty, 2),
        "finding_count": len(applicable_findings),
    }


def compute_trust_score(
    investigation_id: UUID,
    findings: List[Any],
    risk_appetite: str = "balanced",
) -> TrustScoreResponse:
    """Compute overall trust score, confidence, and risk per Section 11.1."""
    dim_scores: List[DimensionScore] = []
    applicable_weights: Dict[Dimension, float] = {}

    weights = dict(DEFAULT_DIMENSION_WEIGHTS)
    if risk_appetite == "conservative":
        weights[Dimension.compliance] *= 1.2
        weights[Dimension.security_privacy] *= 1.2
    elif risk_appetite == "aggressive":
        weights[Dimension.compliance] *= 0.8
        weights[Dimension.security_privacy] *= 0.8

    for dim in Dimension:
        result = compute_dimension_score(findings, dim)
        if result["applicable"]:
            applicable_weights[dim] = weights[dim]
            dim_scores.append(
                DimensionScore(
                    dimension=dim,
                    score=result["score"],
                    weight=weights[dim],
                    confidence=result["confidence"],
                    rationale=f"{result['finding_count']} findings analyzed, total penalty {result['penalties']}",
                )
            )

    # Renormalize applicable weights
    total_applicable_weight = sum(applicable_weights.values())
    if total_applicable_weight > 0:
        for ds in dim_scores:
            ds.weight = round(applicable_weights[ds.dimension] / total_applicable_weight, 3)

    # Overall score & confidence weighted average
    overall_score = 0.0
    overall_confidence = 0.0
    for ds in dim_scores:
        overall_score += ds.score * ds.weight
        overall_confidence += ds.confidence * ds.weight

    # Top risks & missing evidence
    top_risks: List[UUID] = []
    missing_evidence_count = 0
    has_critical_contradiction = False

    for f in findings:
        status = getattr(f, "status", None)
        sev = getattr(f, "severity", None)
        fid = getattr(f, "id", None)

        if isinstance(status, str):
            status = FindingStatus(status)
        if isinstance(sev, str):
            sev = Severity(sev)

        if status == FindingStatus.insufficient_evidence or getattr(f, "missing_evidence", None):
            missing_evidence_count += 1

        if sev in (Severity.critical, Severity.high):
            if fid:
                top_risks.append(fid)

        if sev == Severity.critical and status == FindingStatus.contradictory:
            has_critical_contradiction = True

    # Determine overall risk
    if has_critical_contradiction:
        overall_risk = Severity.critical
    elif overall_score < 50.0:
        overall_risk = Severity.high
    elif overall_score < 75.0:
        overall_risk = Severity.medium
    else:
        overall_risk = Severity.low

    return TrustScoreResponse(
        investigation_id=investigation_id,
        overall_score=round(overall_score, 2),
        score_confidence=round(overall_confidence, 3),
        overall_risk=overall_risk,
        label="Decision-support score. Not a certification.",
        dimensions=dim_scores,
        top_risks=top_risks[:5],
        missing_evidence_count=missing_evidence_count,
    )
