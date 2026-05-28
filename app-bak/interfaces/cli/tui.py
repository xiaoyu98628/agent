import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea

from app.application.chat.service import ChatService
from app.interfaces.cli.commands import handle_slash_command, run_turn_with_renderer
from app.interfaces.cli.render import DIM, RST, cprint, print_banner, print_user_message
from app.interfaces.cli.session import CliSession
from config.config import config


class AgentTui:
    """Hermes-inspired fixed-bottom-input chat TUI."""

    def __init__(self, session: CliSession, chat: ChatService) -> None:
        self.session = session
        self.chat = chat
        self.busy = False
        self._app: Application | None = None
        self._kb = KeyBindings()
        self._input = TextArea(
            height=Dimension(min=1, max=8, preferred=1),
            prompt=self._prompt_fragments,
            multiline=True,
            wrap_lines=True,
            read_only=Condition(lambda: self.busy),
        )
        self._bind_keys()

    def _prompt_fragments(self):
        if self.busy:
            return [("class:prompt-busy", "⚕ ")]
        return [("class:prompt", "❯ ")]

    def _bind_keys(self) -> None:
        @self._kb.add("enter")
        async def submit(event) -> None:
            if self.busy:
                return
            text = self._input.buffer.text.strip()
            if not text:
                return
            self._input.buffer.text = ""
            asyncio.create_task(self._handle_input(text))

        @self._kb.add("escape", "enter")
        @self._kb.add("c-j")
        def newline(event) -> None:
            if self.busy:
                return
            event.current_buffer.insert_text("\n")

        @self._kb.add("c-d")
        def exit_d(event) -> None:
            event.app.exit()

        @self._kb.add("c-c")
        def exit_c(event) -> None:
            if self.busy:
                return
            event.app.exit()

    async def _handle_input(self, text: str) -> None:
        self.busy = True
        if self._app:
            self._app.invalidate()
        try:
            if text.startswith("/"):
                should_continue = await handle_slash_command(text, self.session)
                if not should_continue and self._app:
                    self._app.exit()
                return

            print_user_message(text)
            await run_turn_with_renderer(
                message=text,
                session=self.session,
                chat=self.chat,
                stream=self.session.stream,
            )
        except Exception as exc:
            cprint(f"\n{DIM}Error: {exc}{RST}")
        finally:
            self.busy = False
            if self._app:
                self._app.invalidate()

    async def run(self) -> None:
        configure = config()
        print_banner(deployment_mode=configure.app.deployment_mode, model_label=self.session.model_label())

        style = Style.from_dict(
            {
                "prompt": "bold #FFD700",
                "prompt-busy": "bold ansicyan",
            }
        )
        self._app = Application(
            layout=Layout(self._input),
            key_bindings=self._kb,
            style=style,
            full_screen=False,
        )

        try:
            with patch_stdout():
                await self._app.run_async()
        except (EOFError, KeyboardInterrupt, BrokenPipeError):
            pass
