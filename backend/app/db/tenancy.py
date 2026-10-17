"""
Hospital-level tenancy helper.

Every table that carries hospital_id MUST be filtered through this helper
before returning data to the caller.  This is the single enforcement point
for data isolation between hospitals.

Usage
-----
    from app.db.tenancy import scoped
    from app.models.vendor import Vendor

    stmt = scoped(select(Vendor), Vendor, current_hospital_id)
    result = await db.execute(stmt)
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select

from app.db.base import Base


def scoped(query: Select, model: type[Base], hospital_id: UUID) -> Select:
    """
    Append a ``WHERE model.hospital_id = :hospital_id`` clause to *query*.

    Parameters
    ----------
    query       : SQLAlchemy select() statement to filter.
    model       : The ORM model class.  Must have a ``hospital_id`` column.
    hospital_id : UUID taken from the validated JWT – never from request body.

    Returns
    -------
    The same select() statement with the tenancy predicate added.

    Raises
    ------
    AttributeError : if *model* does not expose a ``hospital_id`` attribute,
                     which is a programming error that should surface immediately.
    """
    if not hasattr(model, "hospital_id"):
        raise AttributeError(
            f"Model {model.__name__!r} has no 'hospital_id' column; "
            "cannot apply tenancy scoping."
        )
    return query.where(model.hospital_id == hospital_id)
