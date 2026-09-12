from typing import Literal

from pydantic import BaseModel, Field


class TurnSummary(BaseModel):
    """What the coding agent didi in this turn?"""

    summary: str = Field(
        description="A concise summary of what the coding agent did in this turn"
    )

    files_touched: list[str] = Field(
        description="Relative paths of the files you read, created, edited",
        default_factory=list
    )

    status: Literal["ok", "needs_input", "failed"] = Field(
        description="ok if request is done, needs_input if you must ask the user, failed if the request failed"
    )