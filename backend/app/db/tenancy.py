"""Tenancy isolation module for KYRO.

Enforces hospital-level data isolation across all queries.
Non-negotiable rule 7: "Every query is scoped by hospital_id taken from the JWT."
"""

import uuid
from typing import Any, Type, TypeVar
from sqlalchemy import Select
from sqlalchemy.orm import DeclarativeBase

T = TypeVar("T", bound=DeclarativeBase)


def scoped(query: Select[Any], model: Type[T], hospital_id: uuid.UUID) -> Select[Any]:
    """Applies hospital_id tenancy filtering to a SQLAlchemy Select query.

    Args:
        query: The SQLAlchemy Select statement to filter.
        model: The ORM model class being queried.
        hospital_id: The UUID of the authenticated hospital from the JWT claims.

    Returns:
        The filtered Select statement with hospital_id isolation applied.

    Raises:
        ValueError: If hospital_id is None or the model cannot be tenant-scoped.
    """
    if hospital_id is None:
        raise ValueError("Tenant isolation violation: hospital_id must not be None")

    # If querying the Hospital table itself, filter by primary key
    if hasattr(model, "__tablename__") and model.__tablename__ == "hospitals":
        return query.where(model.id == hospital_id)

    # Direct hospital_id column on model
    if hasattr(model, "hospital_id"):
        return query.where(model.hospital_id == hospital_id)

    # Models scoped via relationship
    tablename = getattr(model, "__tablename__", None)

    if tablename == "products":
        # products join vendors ON products.vendor_id = vendors.id WHERE vendors.hospital_id = :h
        from app.models.vendor import Vendor
        return query.join(Vendor, model.vendor_id == Vendor.id).where(Vendor.hospital_id == hospital_id)

    if tablename in (
        "agent_runs",
        "timeline_events",
        "steering_commands",
        "debate_messages",
        "dimension_scores",
        "integration_checks",
        "integration_blueprints",
    ):
        from app.models.investigation import Investigation
        return query.join(Investigation, model.investigation_id == Investigation.id).where(
            Investigation.hospital_id == hospital_id
        )

    if tablename == "reviews":
        from app.models.evidence import Finding
        return query.join(Finding, model.finding_id == Finding.id).where(Finding.hospital_id == hospital_id)

    if tablename == "finding_evidence":
        from app.models.evidence import Finding
        return query.join(Finding, model.finding_id == Finding.id).where(Finding.hospital_id == hospital_id)

    if tablename == "requirement_catalogue":
        # Global requirement catalogue is hospital-agnostic
        return query

    raise ValueError(f"Cannot apply tenant isolation to unmapped model: {model.__name__}")
