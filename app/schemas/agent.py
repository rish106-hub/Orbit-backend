from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    text: str = Field(min_length=1)


class CandidateSlot(BaseModel):
    start: datetime
    end: datetime
    score: float


class ProposedAction(BaseModel):
    tool_name: str
    arguments: dict[str, Any]


class AgentQueryResponse(BaseModel):
    run_id: str
    intent: str
    message: str
    requires_confirmation: bool
    proposed_action: ProposedAction | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class AgentExecuteRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
