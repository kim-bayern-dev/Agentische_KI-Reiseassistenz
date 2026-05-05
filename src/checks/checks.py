import os
import requests
from typing import Any


VLLM_BASE_URL = os.getenv("OPENAI_API_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL")
HEALTH_TIMEOUT_SECONDS = float(os.getenv("HEALTH_TIMEOUT_SECONDS", "3.0"))


def check_ollama() -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "reachable": False,
        "model_present": False,
        "base_url": OLLAMA_BASE_URL,
        "required_model": OLLAMA_EMBED_MODEL,
    }

    try:
        resp = requests.get(
            f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags",
            timeout=HEALTH_TIMEOUT_SECONDS,
        )
        result["status_code"] = resp.status_code

        if resp.status_code != 200:
            result["error"] = f"unexpected status {resp.status_code}"
            return result

        result["reachable"] = True
        data = resp.json()

        models = data.get("models", [])
        model_names = [m.get("name", "") for m in models if isinstance(m, dict)]

        result["model_present"] = OLLAMA_EMBED_MODEL in model_names
        result["ok"] = result["reachable"] and result["model_present"]

        if not result["model_present"]:
            result["error"] = f"required model not found: {OLLAMA_EMBED_MODEL}"

        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def check_vllm() -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "reachable": False,
        "authorized": False,
        "model_present": False,
        "base_url": VLLM_BASE_URL,
        "required_model": MODEL_NAME,
    }

    if not MODEL_NAME:
        result["error"] = "MODEL_NAME is empty"
        return result

    if not OPENAI_API_KEY:
        result["error"] = "OPENAI_API_KEY is empty"
        return result

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    try:
        resp = requests.get(
            f"{VLLM_BASE_URL.rstrip('/')}/models",
            headers=headers,
            timeout=HEALTH_TIMEOUT_SECONDS,
        )
        result["status_code"] = resp.status_code
        result["reachable"] = True

        if resp.status_code == 401:
            result["error"] = "unauthorized"
            return result

        if resp.status_code != 200:
            result["error"] = f"unexpected status {resp.status_code}"
            return result

        result["authorized"] = True

        data = resp.json()
        models = data.get("data", [])
        model_ids = [m.get("id", "") for m in models if isinstance(m, dict)]

        result["model_present"] = MODEL_NAME in model_ids
        result["ok"] = result["authorized"] and result["model_present"]

        if not result["model_present"]:
            result["error"] = f"required model not found: {MODEL_NAME}"

        return result

    except Exception as e:
        result["error"] = str(e)
        return result
