from pathlib import Path


def load_text_from_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in {".txt", ".md", ".markdown", ".json", ".csv", ".py", ".yaml", ".yml"}:
        raise ValueError(f"Unsupported file type: {suffix}")
    return path.read_text(encoding="utf-8")


def load_text_from_source(*, content: str | None, file_path: str | None) -> tuple[str, str | None]:
    if content and content.strip():
        return content.strip(), file_path
    if file_path:
        path = Path(file_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        return load_text_from_path(path), str(path)
    raise ValueError("Either content or file_path is required")
