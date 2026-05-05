import uuid
import gradio as gr
from loguru import logger


def init_session(request: gr.Request):
    """Runs once per browser tab (on page load)."""
    session_id = uuid.uuid4().hex
    logger.info(
        f"Initializing new session id: {session_id} for user: {request.username}"
    )

    return [], session_id


def clear_session(_chatbot_value, _current_session_id):
    """Clear chat history and rotate session id."""
    new_session_id = uuid.uuid4().hex
    logger.info(f"Clearing chat and rotating session id to: {new_session_id}")
    return [], new_session_id


def log_logout(request: gr.Request):
    """Log logout event."""
    logger.info(f"User {request.username} logged out.")
