"""Family-scoped commitment dependency action."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.commitment_dependency import CommitmentDependency


# Keep relationship rules and cycle detection in the dedicated dependency service.
async def create_dependency(
    *,
    service: Any,
    family_id: str,
    prerequisite_id: str,
    dependent_id: str,
    relationship: str = "MUST_COMPLETE_BEFORE",
) -> Any:
    """Create a dependency through the service's family and cycle checks."""
    # The registry schema restricts this to MUST_COMPLETE_BEFORE for the MVP.
    # IDs are opaque identifiers; the service must verify that both records exist in this family.
    return await service.create_dependency(
        family_id=family_id,
        prerequisite_id=prerequisite_id,
        dependent_id=dependent_id,
        relationship=relationship,
    )
