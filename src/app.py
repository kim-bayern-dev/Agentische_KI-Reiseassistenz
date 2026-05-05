"""Main entry point for the reise assistant demo app."""

import os
import click
import uvicorn
import gradio as gr
from loguru import logger

from db.embedding import GraniteEmbedder  # for init
from config import AppConfig
from ui import get_ui
from theme import kim_theme
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from checks.checks import check_ollama, check_vllm


@click.command()
def main():
    """Main function to start the Gradio app."""
    config = AppConfig()

    app = FastAPI()

    @app.get("/health")
    def health():
        ollama = check_ollama()
        vllm = check_vllm()

        overall_ok = ollama["ok"] and vllm["ok"]

        payload = {
            "status": "ok" if overall_ok else "unhealthy",
            "checks": {
                "ollama": ollama,
                "vllm": vllm,
            },
        }

        return JSONResponse(
            content=payload,
            status_code=200 if overall_ok else 503,
        )

    gradio_app = get_ui(config=config)

    # set concurrency limit
    gradio_app.queue(default_concurrency_limit=4)

    logger.info("Launching kompass...")
    # mount the gradio app to fastapi
    app = gr.mount_gradio_app(
        app,
        gradio_app,
        path="/",
        auth=[(os.environ.get("APP_USERNAME"), os.environ.get("APP_PASSWORD"))],
        server_name="0.0.0.0",
        server_port=8807,
        favicon_path="assets/favicon.ico",
        css_paths="assets/components.css",
        theme=kim_theme(),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://controlpanel.kim-dev.de",
            "http://controlpanel.kim-dev.de",
        ],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    uvicorn.run(app, host="0.0.0.0", port=8807)


if __name__ == "__main__":
    main()
