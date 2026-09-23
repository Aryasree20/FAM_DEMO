"""Family-scoped expense actions exposed to the agent."""

from __future__ import annotations

from typing import Any


# Each handler accepts the trusted service from application wiring plus validated model arguments.
async def add_expense(
    *,
    service: Any,
    family_id: str,
    amount: float,
    category: str,
    expense_date: str,
    merchant: str | None = None,
    description: str | None = None,
    member_id: str | None = None,
) -> Any:
    """Create one confirmed expense; business rules and family checks belong to the service."""
    # The registry has already rejected missing, malformed, and unexpected model arguments.
    # We pass all supported fields explicitly so the service call is easy to audit.
    # Mark the origin consistently so saved expenses can be distinguished from manual entries.
    return await service.add_expense(
        family_id=family_id,
        amount=amount,
        category=category,
        expense_date=expense_date,
        merchant=merchant,
        description=description,
        member_id=member_id,
        source="agent",
    )


async def get_expense_summary(
    *,
    service: Any,
    family_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
) -> Any:
    """Return database-calculated totals for the requested family and date filters."""
    # A missing start or end date is preserved as None for the service's default-period behavior.
    # Keep aggregation in the repository/service so the model never calculates financial totals itself.
    return await service.get_expense_summary(
        family_id=family_id,
        start_date=start_date,
        end_date=end_date,
        category=category,
    )
