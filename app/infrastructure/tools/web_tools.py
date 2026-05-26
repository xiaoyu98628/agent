import re
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from langchain_core.tools import BaseTool, tool

from app.infrastructure.tools.context import ToolContext


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = False
        if tag in {"p", "br", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self._parts.append(data.strip())

    def text(self) -> str:
        raw = " ".join(self._parts)
        return re.sub(r"\s+", " ", raw).strip()


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, total {len(text)} chars]"


def _validate_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return "Error: only http/https URLs are allowed"
    if not parsed.netloc:
        return "Error: invalid URL"
    return None


def build_web_tools(ctx: ToolContext) -> list[BaseTool]:
    timeout = ctx.web_fetch_timeout_seconds
    max_chars = ctx.max_output_chars

    @tool
    def fetch_webpage(url: str) -> str:
        """Fetch a public HTTP/HTTPS webpage and return plain text content."""
        err = _validate_url(url)
        if err:
            return err
        request = Request(
            url.strip(),
            headers={"User-Agent": "agent/0.2 (+https://github.com/local/agent)"},
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
        except HTTPError as exc:
            return f"Error: HTTP {exc.code} for {url}"
        except URLError as exc:
            return f"Error: failed to fetch {url}: {exc.reason}"
        except TimeoutError:
            return f"Error: request timed out after {timeout}s"

        try:
            html = raw.decode(charset, errors="replace")
        except LookupError:
            html = raw.decode("utf-8", errors="replace")

        parser = _TextExtractor()
        parser.feed(html)
        text = parser.text() or html
        return _truncate(text, max_chars)

    return [fetch_webpage]
