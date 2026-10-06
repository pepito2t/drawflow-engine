"""One conversation turn: the model answers, calling Drawflow tools when it needs them."""

import json
from typing import Any

from engine.assistant.conversation import ChatRequest
from engine.assistant.errors import AssistantError
from engine.assistant.events import (
    DoneEvent,
    EmitAssistant,
    ProposalEvent,
    TextDeltaEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from engine.assistant.messages import t
from engine.assistant.model_client import ModelClient, ModelReply, ToolCall
from engine.assistant.toolbox import ToolBox, ToolOutcome
from engine.core.guide import GuideUnavailableError, sections

MAX_TOOL_ROUNDS = 6
PROPOSAL_SHOWN = t("agent.proposal_shown")
SYSTEM_PROMPT = t("agent.system_prompt")
HELP_TOPICS_HEADING = t("agent.help_topics_heading")
JsonObject = dict[str, Any]


def system_prompt() -> str:
    """Lists the guide's topics up front, so a how-to needs one tool call instead of two."""
    try:
        topics = "; ".join(f"{section.id} : {section.title}" for section in sections())
    except GuideUnavailableError:
        return SYSTEM_PROMPT
    return f"{SYSTEM_PROMPT}\n{HELP_TOPICS_HEADING}{topics}."


async def run_turn(
    request: ChatRequest, model: ModelClient, tools: ToolBox, emit: EmitAssistant
) -> None:
    messages: list[JsonObject] = [{"role": "system", "content": system_prompt()}]
    messages += [message.model_dump() for message in request.recent_history()]
    definitions = await tools.definitions()
    for _ in range(MAX_TOOL_ROUNDS):
        reply = await model.complete(
            messages, definitions, lambda text: emit(TextDeltaEvent(text=text))
        )
        if not reply.tool_calls:
            emit(DoneEvent())
            return
        messages.append(_assistant_message(reply))
        for call in reply.tool_calls:
            messages.append(await _answer_tool_call(call, tools, emit))
    raise AssistantError(
        t("agent.too_many_tool_rounds", rounds=MAX_TOOL_ROUNDS),
        hint=t("agent.too_many_tool_rounds.hint"),
    )


async def _answer_tool_call(call: ToolCall, tools: ToolBox, emit: EmitAssistant) -> JsonObject:
    arguments = _parse_arguments(call.arguments)
    emit(ToolCallEvent(id=call.id, name=call.name, arguments=arguments or {}))
    if arguments is None:
        outcome = ToolOutcome(ok=False, text=t("agent.invalid_arguments"))
    else:
        outcome = await tools.call(call.name, arguments)
    emit(ToolResultEvent(id=call.id, name=call.name, ok=outcome.ok))
    if outcome.proposal is not None:
        emit(ProposalEvent(id=call.id, **outcome.proposal.model_dump()))
        return {"role": "tool", "tool_call_id": call.id, "content": PROPOSAL_SHOWN}
    return {"role": "tool", "tool_call_id": call.id, "content": outcome.text}


def _assistant_message(reply: ModelReply) -> JsonObject:
    return {
        "role": "assistant",
        "content": reply.text,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": call.arguments or "{}"},
            }
            for call in reply.tool_calls
        ],
    }


def _parse_arguments(raw: str) -> JsonObject | None:
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None
