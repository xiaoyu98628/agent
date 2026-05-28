def sanitize_text(text: str | None) -> str:
    """Remove lone surrogate code points that break UTF-8 encode/print/storage."""
    if not text:
        return ""
    return text.encode("utf-8", errors="replace").decode("utf-8")
