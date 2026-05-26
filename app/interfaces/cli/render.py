import os
import shutil

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import ANSI

NO_COLOR = bool(os.environ.get("NO_COLOR"))

ACCENT = "" if NO_COLOR else "\033[38;2;255;215;0m"
GOLD = ACCENT
BOLD = "" if NO_COLOR else "\033[1m"
DIM = "" if NO_COLOR else "\033[2m"
RST = "" if NO_COLOR else "\033[0m"
STREAM_PAD = "    "


def terminal_width(default: int = 80) -> int:
    try:
        return max(40, shutil.get_terminal_size(fallback=(default, 24)).columns)
    except OSError:
        return default


def cprint(text: str) -> None:
    print_formatted_text(ANSI(text))


def escape(text: str) -> str:
    return text.replace("[", "\\[")


def print_banner(*, deployment_mode: str, model_label: str) -> None:
    w = terminal_width()
    line = "─" * min(w - 2, 56)
    cprint(f"\n{GOLD}{BOLD}Agent{RST} {DIM}· personal CLI · {deployment_mode}{RST}")
    cprint(f"{DIM}{line}{RST}")
    cprint(f"{DIM}model {model_label}  ·  /help  ·  Ctrl+D exit{RST}\n")


def print_user_message(text: str) -> None:
    w = min(terminal_width(), 56)
    cprint(f"\n{GOLD}{'─' * w}{RST}")
    for index, line in enumerate(text.splitlines() or [""]):
        if index == 0:
            cprint(f"{GOLD}{BOLD}●{RST} {BOLD}{escape(line)}{RST}")
        else:
            cprint(f"  {BOLD}{escape(line)}{RST}")


def print_assistant_plain(text: str) -> None:
    if not text:
        cprint(f"{DIM}(no response){RST}")
        return
    renderer = StreamRenderer()
    renderer.open()
    for line in text.splitlines():
        cprint(f"{STREAM_PAD}{line}")
    renderer.close()


class StreamRenderer:
    """Hermes-style streaming response box."""

    def __init__(self, label: str = "⚕ Agent") -> None:
        self._label = label
        self._open = False
        self._buf = ""

    def open(self) -> None:
        if self._open:
            return
        self._open = True
        w = terminal_width()
        header = f"╭─ {self._label} "
        fill = max(w - len(header) - 1, 0)
        cprint(f"\n{GOLD}{header}{'─' * fill}╮{RST}")

    def write(self, text: str) -> None:
        if not text:
            return
        if not self._open:
            self.open()
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            cprint(f"{STREAM_PAD}{line}")

    def close(self) -> None:
        if self._buf:
            cprint(f"{STREAM_PAD}{self._buf.rstrip()}")
            self._buf = ""
        if not self._open:
            return
        w = terminal_width()
        cprint(f"{GOLD}╰{'─' * max(w - 2, 0)}╯{RST}\n")
        self._open = False
