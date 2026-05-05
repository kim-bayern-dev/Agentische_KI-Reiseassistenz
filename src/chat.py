import time
from copy import deepcopy
from typing import List
from gradio import ChatMessage

from agents.runner import run_agents
from utils.formatting import inject_source_chips
from constants import TOOL_ICONS


from typing import List


def print_chat_history(history):
    print("FINAL CHAT STATE:")
    for i, msg in enumerate(history):
        if isinstance(msg, dict):
            role = msg.get("role")
            content = msg.get("content")
            metadata = msg.get("metadata")
        else:
            role = getattr(msg, "role", None)
            content = getattr(msg, "content", None)
            metadata = getattr(msg, "metadata", None)

        print(f"{i}:")
        print(f"  role={role!r}")
        print(f"  content={content[:50]} ...")
        print(f"  metadata={metadata!r}")


def _normalize_message_content(content):
    # Plain text stays plain text
    if isinstance(content, str):
        return content

    # Gradio may round-trip text-only content as a list of parts
    # like [{"type": "text", "text": "..."}]
    if isinstance(content, list):
        text_parts = []
        other_parts = []

        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            else:
                other_parts.append(part)

        # If this was text-only multipart content, collapse it back to a string
        if text_parts and not other_parts:
            return "".join(text_parts)

        # Otherwise keep non-text/mixed content as-is
        return content

    return content


def _normalize_history(history):
    normalized = []

    for msg in history or []:
        if isinstance(msg, dict):
            normalized.append(
                ChatMessage(
                    role=msg.get("role", "assistant"),
                    content=_normalize_message_content(msg.get("content")),
                    metadata=deepcopy(msg.get("metadata")) or {},
                    options=deepcopy(msg.get("options")),
                )
            )
        else:
            normalized.append(
                ChatMessage(
                    role=getattr(msg, "role", "assistant"),
                    content=_normalize_message_content(getattr(msg, "content", "")),
                    metadata=deepcopy(getattr(msg, "metadata", None)) or {},
                    options=deepcopy(getattr(msg, "options", None)),
                )
            )

    return normalized


def chat(
    user_msg: str,
    chat_hist: List,
    interests,
    difficulty,
    location: str,
    poi_state,
    gpx_names: List[str],
    options_sections_state,
    details_sections_state,
    session_id: str,
):
    def _as_list(x):
        if x is None:
            return []
        if isinstance(x, list):
            return x
        return getattr(x, "value", None) or []

    def _is_nonempty_text(x) -> bool:
        if x is None:
            return False
        return bool(str(x).strip())

    def _safe_inject(x) -> str:
        if not _is_nonempty_text(x):
            return ""
        try:
            return inject_source_chips(x)
        except Exception:
            # Fall back to raw text if chip injection fails
            return str(x)

    def _cleanup_trailing_empty_assistant():
        # Defensive: remove empty assistant messages that render as typing bubbles
        while chat_hist and getattr(chat_hist[-1], "role", None) == "assistant":
            content = getattr(chat_hist[-1], "content", None)
            if content is None or (isinstance(content, str) and not content.strip()):
                chat_hist.pop()
            else:
                break

    def _append_assistant_if_nonempty(msg: str):
        if _is_nonempty_text(msg):
            chat_hist.append(ChatMessage(role="assistant", content=msg))

    chat_hist = _normalize_history(chat_hist)
    # 1) add user message + immediate yield
    chat_hist.append(ChatMessage(role="user", content=user_msg))
    # add a spinner for the assistant placeholder
    chat_hist.append(ChatMessage(role="assistant", content="<spinner></spinner>"))
    yield "", chat_hist, location, poi_state, gpx_names, options_sections_state, details_sections_state

    # record the starttime
    start_time = time.time()

    interests_list = _as_list(interests)
    difficulty_list = _as_list(difficulty)

    tools_message_index = None
    tools_log = ""

    panel_info = {
        "pois": poi_state,
        "options_sections": options_sections_state,
        "details_sections": details_sections_state,
    }

    # remove the latest message with the spinner
    if chat_hist[-1].content == "<spinner></spinner>":
        chat_hist.pop()

    try:
        for agents_res in run_agents(
            user_msg=user_msg,
            chat_hist=chat_hist,
            interests=interests_list,
            location=location,
            difficulty=difficulty_list,
            panel_info=panel_info,
        ):
            # extract safely
            raw_message = getattr(agents_res, "message", None)
            message = _safe_inject(raw_message)

            options_panel_res = getattr(agents_res, "options_panel", None)
            details_panel_res = getattr(agents_res, "details_panel", None)
            tool_obj = getattr(agents_res, "tool_call", None)

            # keep side states in sync (safe)
            if getattr(agents_res, "pois", None):
                poi_state = agents_res.pois
            if getattr(agents_res, "gpx", None):
                gpx_names = agents_res.gpx

            # options panel
            if options_panel_res:
                safe_opts = []
                for option in options_panel_res:
                    if isinstance(option, dict):
                        c = option.get("content", "")
                        option["content"] = _safe_inject(c)
                        safe_opts.append(option)
                if safe_opts:
                    options_sections_state = safe_opts

            # details panel
            if details_panel_res:
                safe_details = []
                for detail in details_panel_res:
                    if isinstance(detail, dict):
                        c = detail.get("content", "")
                        detail["content"] = _safe_inject(c)
                        safe_details.append(detail)
                if safe_details:
                    details_sections_state = safe_details

            # tool vs assistant message
            if tool_obj:
                tool_name = str(tool_obj)  # IMPORTANT: avoid unhashable keys
                icon = TOOL_ICONS.get(tool_name, "🛠️")

                if tools_message_index is None:
                    tools_message_index = len(chat_hist)
                    # IMPORTANT: non-empty content so it can't render as the "..." bubble
                    chat_hist.append(
                        ChatMessage(
                            role="assistant",
                            content="⏳ Running tools…",
                            metadata={
                                "title": "⏳ Running tools...",
                                "status": "done",
                            },
                        )
                    )

                step_title = f"{icon} Used tool `{tool_name}`"
                step_parts = [f"### {step_title}"]

                if _is_nonempty_text(message):
                    step_parts.append(message)

                tool_args = getattr(agents_res, "tool_args", None)
                if tool_args is not None:
                    step_parts.append(f"**Args:** `{tool_args}`")

                output = getattr(agents_res, "output", None)
                if output is not None:
                    raw_output = str(output)
                    step_parts.append(
                        "<details>"
                        "<summary><b>Show raw output</b></summary>\n\n"
                        f"{raw_output}\n"
                        "</details>"
                    )

                tools_log += "\n\n".join(step_parts) + "\n\n---\n\n"
                chat_hist[tools_message_index] = ChatMessage(
                    role="assistant",
                    content=(tools_log if tools_log.strip() else "⏳ Recherchiere..."),
                    metadata={
                        "title": f"<spinner></spinner> Recherchiere... {icon} `{tool_name}` {'`'+str(list(tool_args.values())[0])+'`' if tool_args else ''}...",
                        "status": "done",
                    },
                )
            else:
                if tools_message_index is not None:
                    end_time = time.time()
                    chat_hist[tools_message_index] = ChatMessage(
                        role="assistant",
                        content=(
                            tools_log if tools_log.strip() else "✅ Tools finished."
                        ),
                        metadata={
                            "title": f"✅ Recherche abgeschlossen ({end_time - start_time:.2f} Sekunden nachgedacht)",
                            "status": "done",
                        },
                    )
                    tools_message_index = None
                # Only append if actually non-empty (prevents bubble)
                _append_assistant_if_nonempty(message)

            _cleanup_trailing_empty_assistant()

            yield (
                "",
                chat_hist,
                location,
                poi_state,
                gpx_names,
                options_sections_state,
                details_sections_state,
            )

    except Exception as e:
        # If anything breaks mid-stream, show an error *in chat* and still end cleanly.
        _cleanup_trailing_empty_assistant()
        chat_hist.append(
            ChatMessage(
                role="assistant",
                content=f"⚠️ Internal error while processing the response: {type(e).__name__}: {e}",
            )
        )
        yield (
            "",
            chat_hist,
            location,
            poi_state,
            gpx_names,
            options_sections_state,
            details_sections_state,
        )
