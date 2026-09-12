from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.agents.structured_output import ProviderStrategy

from configs.config import MAX_MODEL_CALLS_PER_RUN, hitl_enabled
from middlewares.audit import AuditMiddleware
from middlewares.hitl import build_hitl_middleware
from middlewares.protection import ProtectionMiddleware
from models import build_client_model
from prompts import build_system_prompt
from schemas import TurnSummary
from tools import ALL_TOOLS

def build_middleware(
    *,
    enable_hitl: bool
) -> list:
    """
        Harness layers, outermost first.

        1. model-call cap
        2. Audit log
        3. payload guarding
        4. HITL on write/edit/run
    """

    layers: list = [
        ModelCallLimitMiddleware(
            run_limit=MAX_MODEL_CALLS_PER_RUN,
            exit_behavior="end"
        ),
        AuditMiddleware(),
        ProtectionMiddleware()
    ]

    if enable_hitl:
        layers.append(build_hitl_middleware())

    return layers

def build_agent(
    *,
    enable_hitl: bool | None = None,
    extra_guidance: str = "",
):
    model, _provider = build_client_model()
    use_hitl = hitl_enabled() if enable_hitl is None else enable_hitl
    return create_agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=build_system_prompt(extra_guidance=extra_guidance),
        middleware=build_middleware(enable_hitl=use_hitl),
        response_format=ProviderStrategy(TurnSummary),
        name="Coding Agent",
    )