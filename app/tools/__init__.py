"""Controlled tool contracts and family-scoped handler assembly."""

from functools import partial
from typing import Any

from app.tools.commitment_tools import create_commitment, search_commitments, update_commitment
from app.tools.dependency_tools import create_dependency
from app.tools.expense_tools import add_expense, get_expense_summary
from app.tools.priority_tools import get_family_priorities
from app.tools.registry import ToolRegistry, build_registry


# Bind concrete service objects here so individual handlers stay easy to read and reuse.
# The model receives only the generated schemas; it cannot inspect or replace these objects.
def build_tool_registry(
    *,
    expense_service: Any,
    commitment_service: Any,
    dependency_service: Any,
    priority_service: Any,
) -> ToolRegistry:
    """Assemble the seven approved tools around application service instances."""
    # Partial application hides service objects from the model-facing argument schemas.
    # Each handler remains independently callable in focused service-level code.
    handlers = {
        "add_expense": partial(add_expense, service=expense_service),
        "get_expense_summary": partial(get_expense_summary, service=expense_service),
        "create_commitment": partial(create_commitment, service=commitment_service),
        "search_commitments": partial(search_commitments, service=commitment_service),
        "update_commitment": partial(update_commitment, service=commitment_service),
        "create_dependency": partial(create_dependency, service=dependency_service),
        "get_family_priorities": partial(get_family_priorities, service=priority_service),
    }
    # The registry checks that all seven approved actions are present exactly once.
    return build_registry(handlers)


__all__ = ["ToolRegistry", "build_tool_registry", "build_registry"]
