import json, re
from datetime import datetime
from zoneinfo import ZoneInfo
from dataclasses import dataclass
from typing import List, Generator, Dict, Any

from loguru import logger

from tools import call_tool
from tools.registry import ToolRegistry
from llm import CLIENT, MODEL_NAME
from llm.prompts import AGENT_PROMPT
from agents.output_models import StructuredResponse

GradioMessages = List[Dict[str, Any]]


@dataclass
class AgentResponse:
    message: str | None = None
    output: str | None = None
    options_panel: List[dict] | None = None
    pois: List[str] | None = None
    gpx: str | None = None
    details_panel: List[dict] | None = None
    tool_call: str | None = None
    tool_args: dict | None = None


@dataclass
class ToolCallResponse:
    content: str
    tool_call: str
    tool_args: dict


@dataclass
class ThinkingResponse:
    message: str


def gradio_messages_to_responses_input(history: GradioMessages) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for m in history:
        try:
            role = m.role
            content = m.content
        except AttributeError:
            role = m["role"]
            content = m["content"]

        if role in ("user", "assistant", "system") and content is not None:
            # vLLM / OpenAI-compatible servers are happiest if content is a plain string
            if not isinstance(content, str):
                content = json.dumps(content, ensure_ascii=False)
            items.append({"role": role, "content": content})

    return items


def _response_item_to_input_item(item: Any) -> Dict[str, Any]:
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if isinstance(item, dict):
        return item
    raise TypeError(f"Cannot convert response item to input item: {type(item)!r}")


def _extract_reasoning_text(output_items: List[Any]) -> List[str]:
    snippets: List[str] = []

    def add_text(value: Any) -> None:
        if not value:
            return
        if isinstance(value, str):
            text = value.strip()
            if text:
                snippets.append(text)
            return
        if isinstance(value, dict):
            text = (
                value.get("text") or value.get("content") or value.get("summary_text")
            )
            if isinstance(text, str) and text.strip():
                snippets.append(text.strip())
            return

        text = (
            getattr(value, "text", None)
            or getattr(value, "content", None)
            or getattr(value, "summary_text", None)
        )
        if isinstance(text, str) and text.strip():
            snippets.append(text.strip())

    for item in output_items:
        if getattr(item, "type", None) != "reasoning":
            continue

        summary = getattr(item, "summary", None)
        if summary:
            if isinstance(summary, list):
                for part in summary:
                    add_text(part)
            else:
                add_text(summary)

        content = getattr(item, "content", None)
        if content:
            if isinstance(content, list):
                for part in content:
                    add_text(part)
            else:
                add_text(content)

    return snippets


def _safe_json_loads(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except Exception:
        return {"raw": raw}


def _coerce_tool_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def _strip_json_code_fences(text: str) -> str:
    raw = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    return match.group(1).strip() if match else raw


def _parse_structured_response(text: str) -> dict:
    try:
        return StructuredResponse.model_validate_json(text).model_dump()
    except Exception:
        cleaned = _strip_json_code_fences(text)
        return StructuredResponse.model_validate_json(cleaned).model_dump()


def _build_initial_input(
    chat_hist: List,
    interests: List,
    difficulty: List,
    location: str,
    panel_info: dict,
) -> tuple[List[Dict[str, Any]], Any]:
    input_items = gradio_messages_to_responses_input(chat_hist)

    instructions = AGENT_PROMPT.format(
        location=location,
        interests=", ".join(interests),
        difficulty=", ".join(difficulty),
        datetime=datetime.now(ZoneInfo("Europe/Berlin")).strftime(
            "%Y-%m-%d %H:%M:%S %Z%z"
        ),
    )

    input_items.insert(0, {"role": "system", "content": instructions})

    if panel_info:
        input_items.append(
            {
                "role": "user",
                "content": (
                    "This is the current state of the panel info, you can extend and modify it. "
                    "Keep as much as reasonably possible in your response if still usable:\n\n"
                    f"existing pois: {panel_info.get('pois')}\n"
                    f"existing options_panel: {panel_info.get('options_sections')}\n"
                    f"existing details_panel: {panel_info.get('details_sections')}\n\n"
                ),
            }
        )

    return input_items


def _build_final_format_request(
    agent_context: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    final_instruction = {
        "role": "user",
        "content": (
            "Now produce the final answer only as JSON matching the provided schema exactly. "
            "Use the conversation, your previous reasoning, and all tool outputs above. "
            "Do not call tools. Do not include markdown fences. Do not add any extra text."
        ),
    }
    return [*agent_context, final_instruction]


def run_agents(
    user_msg: str,
    chat_hist: List,
    interests: List,
    difficulty: List,
    location: str,
    panel_info: dict,
) -> Generator[AgentResponse]:
    """Run the agent loop with tools first, then a final structured-output pass."""

    tool_registry = ToolRegistry()
    agent_context = _build_initial_input(
        chat_hist=chat_hist,
        interests=interests,
        difficulty=difficulty,
        location=location,
        panel_info=panel_info,
    )

    thinking_log: List[str] = []

    # Phase 1: normal agentic/tool loop without text.format
    while True:
        resp = CLIENT.responses.create(
            model=MODEL_NAME,
            input=agent_context,
            temperature=1.0,
            tools=tool_registry.TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,
        )
        thinking_msg = _extract_reasoning_text(resp.output)
        if thinking_msg:
            yield AgentResponse(
                message="\n".join(thinking_msg),
                output={},
                tool_call="thinking",
                tool_args={},
            )

        thinking_log.extend(thinking_msg)

        # IMPORTANT: keep ALL output items, including reasoning + function calls,
        # so the model can continue reasoning correctly after tool execution.
        out_items = [_response_item_to_input_item(it) for it in resp.output]
        agent_context.extend(out_items)

        tool_calls = [
            it for it in resp.output if getattr(it, "type", None) == "function_call"
        ]

        if not tool_calls:
            break

        for call in tool_calls:
            call_id = getattr(call, "call_id", None) or getattr(call, "id", None)
            if not call_id:
                raise RuntimeError(f"Tool call without call_id/id: {call}")

            try:
                result = call_tool(call)
                tool_output = _coerce_tool_output(result.get("content"))
                tool_args = result.get("tool_args") or _safe_json_loads(
                    getattr(call, "arguments", None)
                )
            except Exception as e:
                logger.exception(
                    "Tool execution failed for {}", getattr(call, "name", "<unknown>")
                )
                tool_output = f"Tool error: {type(e).__name__}: {e}"
                tool_args = _safe_json_loads(getattr(call, "arguments", None))

            agent_context.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": tool_output,
                }
            )

            yield AgentResponse(
                output=tool_output,
                tool_call=getattr(call, "name", None),
                tool_args=tool_args,
            )

    # Phase 2: final structured-output pass, with NO tools exposed
    final_resp = CLIENT.responses.create(
        model=MODEL_NAME,
        input=_build_final_format_request(agent_context),
        temperature=1.0,
        text={
            "format": {
                "type": "json_schema",
                "name": "structured_response",
                "strict": True,
                "schema": StructuredResponse.model_json_schema(),
            }
        },
    )

    final_text = final_resp.output_text or ""

    thinking_msg = _extract_reasoning_text(final_resp.output)
    if thinking_msg:
        yield AgentResponse(
            message="\n".join(thinking_msg),
            output={},
            tool_call="thinking",
            tool_args={},
        )

    try:
        response = _parse_structured_response(final_text)
    except Exception as e:
        logger.exception("Failed to parse the final structured response: {}", e)
        response = {
            "message": (
                "Entschuldigung, es gab ein Problem bei der Erstellung der Antwort.\n\n"
                f"{final_text}"
            ),
            "options_panel": [],
            "pois": [],
            "gpx": None,
            "details_panel": [],
        }

    if isinstance(response, dict):
        yield AgentResponse(
            message=response.get("message", ""),
            options_panel=response.get("options_panel"),
            pois=response.get("pois"),
            gpx=response.get("gpx"),
            details_panel=response.get("details_panel"),
        )
        return

    if isinstance(response, list):
        for res in response:
            yield AgentResponse(
                message=res.get("message", ""),
                options_panel=res.get("options_panel"),
                pois=res.get("pois"),
                gpx=res.get("gpx"),
                details_panel=res.get("details_panel"),
            )
        return

    logger.error("Unexpected response format: {}", type(response))
    yield AgentResponse(
        message="Entschuldigung, es gab ein Problem bei der Erstellung der Antwort.",
    )
