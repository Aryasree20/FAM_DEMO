"""Family priority action exposed to the agent."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.commitment import Commitment
from app.models.commitment_dependency import CommitmentDependency
from typing import Any


# Ranking remains deterministic in the priority service; the LLM only explains returned evidence.
async def get_family_priorities(
    *,
    service: Any,
    family_id: str,
    as_of: str | None = None,
    limit: int = 10,
) -> Any:
    """Return deterministic priority results, including their evidence."""
    # Keep requested result size bounded so the model receives focused, relevant context.
    # If as_of is omitted, the service selects the current date in the family's timezone.
    return await service.get_family_priorities(
        family_id=family_id,
        as_of=as_of,
        limit=limit,
    )
