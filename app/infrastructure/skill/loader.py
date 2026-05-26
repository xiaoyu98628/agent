import re
from pathlib import Path

from app.domain.skill.entity import SkillContent, SkillInfo
from app.domain.skill.exceptions import SkillNotFoundError
from config.config import config

_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def _parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    body = raw[match.end() :]
    return meta, body


def _skills_root() -> Path:
    configure = config()
    root = Path(configure.skills.skills_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _relative_skill_path(skill_file: Path, root: Path) -> str:
    rel = skill_file.parent.relative_to(root)
    return str(rel).replace("\\", "/")


def _category_from_relative(relative_path: str) -> str | None:
    parts = relative_path.split("/")
    if len(parts) > 1:
        return parts[0]
    return None


def scan_skills() -> list[SkillInfo]:
    root = _skills_root()
    skills: list[SkillInfo] = []
    for skill_file in sorted(root.rglob("SKILL.md")):
        raw = skill_file.read_text(encoding="utf-8")
        meta, _ = _parse_frontmatter(raw)
        name = meta.get("name") or skill_file.parent.name
        description = meta.get("description") or ""
        relative_path = _relative_skill_path(skill_file, root)
        skills.append(
            SkillInfo(
                name=name,
                description=description,
                category=_category_from_relative(relative_path),
                relative_path=relative_path,
            )
        )
    return skills


def load_skill(name: str) -> SkillContent:
    target = name.strip().lower()
    for info in scan_skills():
        if info.name.lower() == target or info.relative_path.lower().endswith(f"/{target}") or info.relative_path.lower() == target:
            skill_file = _skills_root() / info.relative_path / "SKILL.md"
            if not skill_file.is_file() and info.relative_path == info.name:
                skill_file = _skills_root() / info.name / "SKILL.md"
            raw = skill_file.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(raw)
            resolved = SkillInfo(
                name=meta.get("name") or info.name,
                description=meta.get("description") or info.description,
                category=info.category,
                relative_path=info.relative_path,
            )
            return SkillContent(info=resolved, body=body.strip(), raw=raw)
    raise SkillNotFoundError(f"Skill not found: {name}")


def save_skill(*, name: str, description: str, body: str, category: str | None = None) -> SkillInfo:
    root = _skills_root()
    folder = root / category / name if category else root / name
    folder.mkdir(parents=True, exist_ok=True)
    skill_file = folder / "SKILL.md"
    content = f"---\nname: {name}\ndescription: {description}\n---\n\n{body.strip()}\n"
    skill_file.write_text(content, encoding="utf-8")
    relative_path = _relative_skill_path(skill_file, root)
    return SkillInfo(name=name, description=description, category=category, relative_path=relative_path)


def build_skills_prompt_index() -> str:
    configure = config()
    if not configure.skills.enabled:
        return ""
    skills = scan_skills()
    if not skills:
        return ""
    lines = ["<available_skills>"]
    for skill in skills:
        category = f" [{skill.category}]" if skill.category else ""
        lines.append(f"- {skill.name}{category}: {skill.description}")
    lines.append("</available_skills>")
    lines.append("When a skill is relevant, call skill_view before following specialized instructions.")
    return "\n".join(lines)
