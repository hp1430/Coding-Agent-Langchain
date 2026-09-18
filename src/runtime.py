from dataclasses import dataclass
from typing import Any

from langgraph.types import Command

from messages import last_ai_text, last_tool_text
from schemas import TurnSummary

@dataclass
class AgentTurnResult:
    text: str   #representsagents reply
    structured: TurnSummary | None
    messages: list[Any]
    pending_interrupt: dict[str, Any] | None

def _as_summary(value: Any) -> TurnSummary | None:
    if value is None:
        return None
    if isinstance(value, TurnSummary):
        return value
    if isinstance(value, dict):
        try:
            return TurnSummary.model_validate(value)
        except Exception:
            return None
    return None

def parse_invoke_result(result: Any) -> AgentTurnResult:
    interrupts = tuple(getattr(result, "interrupts", ()) or ())
    # get the complere graph state using the value property
    value = getattr(result, "value", result)
    if not isinstance(value, dict):
        value = {}

    messages = value.get("messages") or []

    if interrupts:
        payload = interrupts[0].value
        return AgentTurnResult(
            text="",
            structured=None,
            messages=messages,
            pending_interrupt=payload
        )

    return AgentTurnResult(
        text=last_ai_text(messages) or last_tool_text(messages),
        structured=_as_summary(value.get("structured_response")),
        messages=messages,
        pending_interrupt=None
    )

def start_turn(agent, user_text: str, config: dict) -> AgentTurnResult:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_text}]},
        config=config,
        version="v2"
    )
    return parse_invoke_result(result)

def resume_turn(agent, decisions: list[dict], config: dict) -> AgentTurnResult:
    result = agent.invoke(
        Command(resume={
            "decisions": decisions
        }),
        config=config,
        version="v2"
    )
    return parse_invoke_result(result)