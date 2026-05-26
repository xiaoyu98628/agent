from pathlib import Path


class PathGuardError(ValueError):
    pass


class PathGuard:
    """将相对路径解析到 workspace 内，禁止目录穿越。"""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def resolve(self, relative_path: str) -> Path:
        clean = relative_path.strip() or "."
        if clean.startswith(("/", "\\")) or (len(clean) > 1 and clean[1] == ":"):
            raise PathGuardError(f"Path must be relative to workspace: {relative_path}")
        target = (self._root / clean).resolve()
        if not target.is_relative_to(self._root):
            raise PathGuardError(f"Path escapes workspace: {relative_path}")
        return target
