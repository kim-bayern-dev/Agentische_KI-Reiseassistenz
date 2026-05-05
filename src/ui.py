import os
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Sequence, TypedDict, List

import gradio as gr
from loguru import logger

from chat import chat
from mapping.map_view import render_map_html
from utils.session import clear_session, init_session

ASSETS_DIR = Path("assets").resolve()
gr.set_static_paths(paths=[ASSETS_DIR])


HEADER_HTML = """
<header id="kim-header">
  <div class="kh-left">
    <div class="kh-logo">🧭</div>
    <div class="kh-brand">
      <div class="kh-title">TrekKI</div>
      <div class="kh-subtitle">Dein Reise-Assistent</div>
    </div>
  </div>

  <img
    src="gradio_api/file=assets/kim-logo.png"
    alt="KIM"
    class="kh-center-logo"
  />

  <nav class="kh-nav">
    <a href="/" id="header-reset-btn" class="kh-link kh-link-danger">Reset</a>
    <a href="/logout" id="header-logout-btn" class="kh-link kh-link-danger">Logout</a>
  </nav>
</header>
"""


class Section(TypedDict, total=False):
    title: str
    content: str
    image_file: str


@dataclass
class UIState:
    """All persistent UI state objects live here."""

    poi_state: gr.State
    gpx_state: gr.State
    session_id: gr.State
    options_sections_state: gr.State
    details_sections_state: gr.State


@dataclass
class SidebarComponents:
    destination: gr.Dropdown
    interests: gr.CheckboxGroup
    difficulty: gr.CheckboxGroup


@dataclass
class MainComponents:
    chatbot: gr.Chatbot
    user_box: gr.Textbox


class kimUI:

    def __init__(self, config: Any, examples: Optional[List[str]] = None):
        self.config = config
        self.examples = examples
        if not examples:
            self.examples = [
                "Wo kann ich am Wochenende wandern gehen?",
                "Welche Tour bietet sich mit Kinderwagen an?",
                "Kann ich eine schöne Runde mit Seeüberquerung drehen?",
                "Welche Wanderungen erreiche ich mit dem öffentlichen Nahverkehr am besten?",
            ]

        self.state: Optional[UIState] = None
        self.sidebar: Optional[SidebarComponents] = None
        self.main: Optional[MainComponents] = None
        self.app: Optional[gr.Blocks] = None

    def build(self) -> gr.Blocks:
        with gr.Blocks(
            analytics_enabled=False,
            title="TrekKI",
            fill_width=True,
        ) as app:
            self.app = app
            self.state = self._init_state()
            gr.HTML(HEADER_HTML)
            with gr.Row():
                self.sidebar = self._build_sidebar()
                self.main = self._build_main_area()

            self._wire_events()

        return app

    def _init_state(self) -> UIState:
        return UIState(
            poi_state=gr.State(None),  # store current POIs
            gpx_state=gr.State([]),
            session_id=gr.State(None),  # current session id
            options_sections_state=gr.State([]),  # rendered planning options
            details_sections_state=gr.State([]),  # rendered details
        )

    def _build_sidebar(self) -> SidebarComponents:
        location_choices = list(self.config.EXAMPLE_LOCATIONS.keys())

        with gr.Column(scale=1, elem_classes=["kim-card"]):
            interests = gr.CheckboxGroup(
                choices=self.config.INTERESTS,
                label="Personalisierung",
                info="Wähle deine Interessen und persönliche Präferenzen aus",
                elem_classes=["tag-checkboxgroup"],
            )

            difficulty = gr.CheckboxGroup(
                choices=["blau", "rot", "schwarz"],
                label="Schwierigkeitsgrad der Touren",
                info="Wähle den Schwierigkeitsgrad der vorgeschlagenen Touren aus",
                elem_classes=["tag-checkboxgroup"],
            )

            destination = gr.Dropdown(
                choices=location_choices,
                label="Aktueller Standort",
                value=location_choices[0],
                visible=True,
                scale=1,
            )

        return SidebarComponents(
            destination=destination,
            interests=interests,
            difficulty=difficulty,
        )

    def _build_main_area(self) -> MainComponents:
        assert self.state is not None

        with gr.Column(scale=5):
            with gr.Row():
                with gr.Column(scale=3, elem_id="kim-chatpanel"):
                    with gr.Group(elem_classes=["kim-card"]):
                        chatbot = gr.Chatbot(
                            scale=3,
                            avatar_images=(None, None),
                            render_markdown=True,
                            allow_tags=["src-chip", "src-tip"],
                            sanitize_html=False,
                            height=700,
                            show_label=False,
                            buttons=["copy"],
                            examples=[{"text": ex} for ex in self.examples],
                            elem_id="kim-chatbox",
                        )

                        user_box = gr.Textbox(
                            submit_btn=True,
                            placeholder="Deine Frage zur Reiseplanung...",
                            label="Anfrage",
                            show_label=False,
                            elem_id="kim-chatbar",
                        )

                with gr.Column(scale=3):
                    self._build_right_panel()

        return MainComponents(
            chatbot=chatbot,
            user_box=user_box,
        )

    def _build_right_panel(self) -> None:
        """
        Builds the map + panels column. The render functions are registered here
        so their outputs appear next to the chat (not below it).
        """
        assert self.state is not None
        assert self.sidebar is not None

        destination = self.sidebar.destination
        poi_state = self.state.poi_state
        gpx_state = self.state.gpx_state
        options_state = self.state.options_sections_state
        details_state = self.state.details_sections_state

        with gr.Column():
            with gr.Row():
                with gr.Column(elem_classes=["kim-card"]):

                    @gr.render(inputs=[destination, poi_state, gpx_state])
                    def _render_map(dest: str, poi: Any, gpx: str):
                        return gr.HTML(
                            value=render_map_html(dest, poi, gpx), elem_id="trip-map"
                        )

            with gr.Column():
                with gr.Row():
                    with gr.Column(elem_classes=["kim-card"]):

                        @gr.render(inputs=options_state)
                        def _render_options(options: Sequence[Section]):
                            self._render_sections(
                                heading="### Optionen zur Reiseplanung",
                                empty_text="_No options yet._",
                                sections=list(options) if options else [],
                                include_images=True,
                                key_prefix="options",
                            )

                    with gr.Column(elem_classes=["kim-card"]):

                        @gr.render(inputs=details_state)
                        def _render_details(details: Sequence[Section]):
                            self._render_sections(
                                heading="### Reisedetails",
                                empty_text="_No details yet._",
                                sections=list(details) if details else [],
                                include_images=False,
                                key_prefix="details",
                            )

    def _render_sections(
        self,
        heading: str,
        empty_text: str,
        sections: list[Section],
        include_images: bool,
        key_prefix: str,
    ) -> None:
        with gr.Column():
            gr.Markdown(value=heading)
            if not sections:
                gr.Markdown(empty_text)
                return

            with gr.Group():
                for i, s in enumerate(sections):
                    title = s.get("title") or f"Section {i + 1}"
                    content = s.get("content") or ""

                    with gr.Accordion(title, open=False, key=f"{key_prefix}-sec-{i}"):
                        gr.HTML(content)
                        if include_images:
                            self._maybe_render_image(s)

    def _maybe_render_image(self, section: Section) -> None:
        image = section.get("image_file")
        if not image:
            return

        path = f"data/images/{image}"
        try:
            gr.Image(path, interactive=False, show_label=False)
        except Exception:
            logger.error(f"Failed to display image: {path}")
            gr.Image(None, visible=False, interactive=False, show_label=False)

    # Events

    def _wire_events(self) -> None:
        assert self.state is not None
        assert self.sidebar is not None
        assert self.main is not None
        assert self.app is not None

        self.main.user_box.submit(
            chat,
            inputs=[
                self.main.user_box,
                self.main.chatbot,
                self.sidebar.interests,
                self.sidebar.difficulty,
                self.sidebar.destination,
                self.state.poi_state,
                self.state.gpx_state,
                self.state.options_sections_state,
                self.state.details_sections_state,
                self.state.session_id,
            ],
            outputs=[
                self.main.user_box,
                self.main.chatbot,
                self.sidebar.destination,
                self.state.poi_state,
                self.state.gpx_state,
                self.state.options_sections_state,
                self.state.details_sections_state,
            ],
            concurrency_limit=4,
            trigger_mode="once",
        )

        def example_to_text(evt: gr.SelectData):
            v = evt.value
            if isinstance(v, dict):
                return v.get("text") or v.get("display_text") or ""
            return str(v)

        self.main.chatbot.example_select(
            example_to_text,
            inputs=None,
            outputs=[self.main.user_box],
            queue=False,
        ).then(
            chat,
            inputs=[
                self.main.user_box,
                self.main.chatbot,
                self.sidebar.interests,
                self.sidebar.difficulty,
                self.sidebar.destination,
                self.state.poi_state,
                self.state.gpx_state,
                self.state.options_sections_state,
                self.state.details_sections_state,
                self.state.session_id,
            ],
            outputs=[
                self.main.user_box,
                self.main.chatbot,
                self.sidebar.destination,
                self.state.poi_state,
                self.state.gpx_state,
                self.state.options_sections_state,
                self.state.details_sections_state,
            ],
            concurrency_limit=4,
            trigger_mode="once",
        )

        # Initialize state & session_id once per browser session (tab/window)
        self.app.load(
            init_session,
            inputs=None,
            outputs=[
                self.main.chatbot,
                self.state.session_id,
            ],
            js="() => { document.body.classList.remove('dark'); document.body.classList.add('light');}",
        )

        # chatbot clear event for history/session only
        self.main.chatbot.clear(
            fn=clear_session,
            inputs=[self.main.chatbot, self.state.session_id],
            outputs=[self.main.chatbot, self.state.session_id],
        )


def get_ui(config: Any) -> gr.Blocks:
    """kim ui factory."""
    return kimUI(config).build()
