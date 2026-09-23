"""Validated, family-scoped registry for the agent's approved actions."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def _validate_iso_date(value: str) -> str:
    """Reject impossible calendar dates while preserving the ISO string for services."""
    # The regex in IsoDate checks the YYYY-MM-DD shape before this checks the real date.
    date.fromisoformat(value)
    return value


# Pattern helps the model emit the expected shape; the validator also rejects dates like February 31.
IsoDate = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$"), AfterValidator(_validate_iso_date)]


class ToolInput(BaseModel):
    """Base input contract; reject model-generated fields we did not approve."""

    model_config = ConfigDict(extra="forbid")


class AddExpenseInput(ToolInput):
    """Arguments needed to record a single household expense."""

    # Explain units and meaning so the model does not confuse totals with individual amounts.
    amount: float = Field(gt=0, allow_inf_nan=False, description="Positive amount in the family's currency.")
    category: str = Field(min_length=1, max_length=80, description="Short category, such as groceries or utilities.")
    expense_date: IsoDate = Field(description="Date the expense happened, in YYYY-MM-DD format.")
    merchant: str | None = Field(default=None, max_length=200, description="Store, provider, or payee, if known.")
    description: str | None = Field(default=None, max_length=2000, description="Short factual note about the expense.")
    member_id: str | None = Field(default=None, min_length=1, description="Existing family member ID, if applicable.")


class ExpenseSummaryInput(ToolInput):
    """Optional inclusive filters for querying saved expense totals."""

    # Both range edges are inclusive; omitted dates let the service choose its normal reporting period.
    start_date: IsoDate | None = Field(default=None, description="Inclusive start date, YYYY-MM-DD; omit for the default period.")
    end_date: IsoDate | None = Field(default=None, description="Inclusive end date, YYYY-MM-DD; omit for the default period.")
    category: str | None = Field(default=None, max_length=80, description="Optional exact expense category filter.")


class CreateCommitmentInput(ToolInput):
    """Fields used to create a household commitment from confirmed user details."""

    # Provide a concise title and preserve uncertainty by leaving unknown optional details null.
    title: str = Field(min_length=1, max_length=300, description="Concise name of the task, bill, appointment, or obligation.")
    commitment_type: str = Field(min_length=1, max_length=50, description="Type such as task, bill, appointment, test, or education.")
    due_date: IsoDate | None = Field(default=None, description="Due date in YYYY-MM-DD format, or null if unknown.")
    amount: float | None = Field(default=None, gt=0, allow_inf_nan=False, description="Positive amount if this commitment has a known cost.")
    member_id: str | None = Field(default=None, min_length=1, description="Existing family member ID responsible for this item, if known.")
    description: str | None = Field(default=None, max_length=2000, description="Relevant details that do not fit in the title.")
    source: str = Field(default="agent", max_length=50, description="Origin label; normally leave as agent.")


class SearchCommitmentsInput(ToolInput):
    """Bounded filters for finding existing household commitments."""

    # Search stays bounded to return manageable context to the model.
    query: str | None = Field(default=None, max_length=300, description="Words from the commitment title or details.")
    status: Literal["open", "completed", "cancelled"] | None = Field(
        default=None, description="Optional status filter: open, completed, or cancelled."
    )
    due_before: IsoDate | None = Field(default=None, description="Include commitments due on or before this YYYY-MM-DD date.")
    due_after: IsoDate | None = Field(default=None, description="Include commitments due on or after this YYYY-MM-DD date.")
    member_id: str | None = Field(default=None, min_length=1, description="Optional existing family member ID filter.")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of matches to return (1 to 100).")


class UpdateCommitmentInput(ToolInput):
    """Allowlisted changes for a commitment that already exists."""

    # Only these fields can be changed; service logic still decides whether a transition is allowed.
    commitment_id: str = Field(min_length=1, description="ID of the existing commitment to update.")
    title: str | None = Field(default=None, min_length=1, max_length=300, description="New title; omit to keep the current title.")
    due_date: IsoDate | None = Field(default=None, description="New YYYY-MM-DD due date; omit to keep the current date.")
    status: Literal["open", "completed", "cancelled"] | None = Field(
        default=None, description="New status: open, completed, or cancelled."
    )
    amount: float | None = Field(default=None, gt=0, allow_inf_nan=False, description="New positive amount, if applicable.")
    member_id: str | None = Field(default=None, min_length=1, description="New existing family member ID, if applicable.")
    description: str | None = Field(default=None, max_length=2000, description="Replacement factual details.")


class CreateDependencyInput(ToolInput):
    """Direction and type of a prerequisite link between two commitments."""

    # Direction matters: prerequisite_id must be completed before dependent_id.
    prerequisite_id: str = Field(min_length=1, description="ID of the commitment that must happen first.")
    dependent_id: str = Field(min_length=1, description="ID of the commitment that is blocked until the prerequisite is done.")
    relationship: str = Field(default="MUST_COMPLETE_BEFORE", pattern="^MUST_COMPLETE_BEFORE$", description="Use MUST_COMPLETE_BEFORE.")


class FamilyPrioritiesInput(ToolInput):
    """Controls how many deterministic priority results to retrieve."""

    # The deterministic service ranks items; the model should report its evidence rather than invent a ranking.
    as_of: IsoDate | None = Field(default=None, description="Evaluate deadlines as of YYYY-MM-DD; omit to use today.")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of ranked priorities to return (1 to 50).")


Handler = Callable[..., Awaitable[Any]]


@dataclass(frozen=True)
class Tool:
    """One model-visible function and its trusted Python handler."""

    name: str
    description: str
    input_model: type[ToolInput]
    handler: Handler

    def model_schema(self) -> dict[str, Any]:
        """Return the JSON Schema format used by model tool calling APIs."""
        # Keep each definition in the conventional function-calling envelope expected by model APIs.
        # The handler object stays private; only name, guidance, and input schema go to the model.
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_model.model_json_schema(),
            },
        }


class ToolRegistry:
    """Dispatch approved actions with server-supplied family scope."""

    def __init__(self, tools: list[Tool]) -> None:
        # Index by name for constant-time dispatch after a model requests an action.
        self._tools = {tool.name: tool for tool in tools}
        # Duplicate names would make dispatch order-dependent, so reject them at construction.
        if len(self._tools) != len(tools):
            raise ValueError("Tool names must be unique")

    @property
    def definitions(self) -> list[dict[str, Any]]:
        # Return fresh schema dictionaries; callers can pass these to the model client.
        return [tool.model_schema() for tool in self._tools.values()]

    async def invoke(
        self, name: str, arguments: Mapping[str, Any] | str, *, family_id: str
    ) -> Any:
        """Decode, validate, and invoke one tool inside the trusted family scope."""
        # Family scope is supplied by the application, never accepted from model-generated arguments.
        if not family_id:
            raise ValueError("family_id is required")
        # Model providers commonly return arguments as either a parsed object or a JSON string.
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise ValueError("Tool arguments must be valid JSON") from exc
        if not isinstance(arguments, Mapping):
            raise ValueError("Tool arguments must be a JSON object")
        # Unknown names are rejected instead of falling back to a default action.
        try:
            tool = self._tools[name]
        except KeyError as exc:
            raise ValueError(f"Unknown tool: {name}") from exc
        # Pydantic rejects missing, mistyped, out-of-range, and unexpected arguments here.
        payload = tool.input_model.model_validate(arguments)
        # Exclude omitted values so handlers can apply their own defaults.
        return await tool.handler(family_id=family_id, **payload.model_dump(exclude_unset=True))


def build_registry(handlers: Mapping[str, Handler]) -> ToolRegistry:
    """Bind business handlers without exposing arbitrary Python or database access."""
    # Descriptions tell the model when to call each action and what evidence it should pass.
    contracts: tuple[tuple[str, str, type[ToolInput]], ...] = (
        ("add_expense", "Record one confirmed household expense. Use only when the user provided the amount, date, and category; do not infer missing values.", AddExpenseInput),
        ("get_expense_summary", "Get database totals and category breakdowns for household expenses. Use for spending or expense-history questions.", ExpenseSummaryInput),
        ("create_commitment", "Create a task, bill, appointment, test, or other household obligation. Use only when the user asks to track it; keep unknown optional details null.", CreateCommitmentInput),
        ("search_commitments", "Find existing household commitments before creating or discussing one. Use filters from the user's request and keep the result limit small.", SearchCommitmentsInput),
        ("update_commitment", "Change only the supplied fields of an existing commitment. Search first if the target ID is unknown; never guess an ID.", UpdateCommitmentInput),
        ("create_dependency", "Record that one commitment must be completed before another. Call only when the user states this prerequisite relationship.", CreateDependencyInput),
        ("get_family_priorities", "Get deterministic ranked household priorities with reasons and evidence. Use for questions about what the family should handle next.", FamilyPrioritiesInput),
    )
    # Compute both directions so missing implementations and accidental extra tools are visible.
    # Fail startup on wiring mistakes rather than silently exposing an incomplete tool set.
    missing = [name for name, _, _ in contracts if name not in handlers]
    extra = set(handlers) - {name for name, _, _ in contracts}
    if missing or extra:
        raise ValueError(f"Handler mismatch; missing={missing}, unexpected={sorted(extra)}")
    # Preserve the documented contract order for predictable model prompts and logs.
    return ToolRegistry([Tool(name, description, model, handlers[name]) for name, description, model in contracts])
