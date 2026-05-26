import json

from app.domain.skill.entity import SkillContent, SkillInfo
from app.domain.skill.exceptions import SkillNotFoundError
from app.infrastructure.skill.loader import build_skills_prompt_index, load_skill, save_skill, scan_skills
from config.config import config


class SkillService:
    def build_prompt_index(self) -> str:
        return build_skills_prompt_index()

    def list_skills(self) -> list[SkillInfo]:
        if not config().skills.enabled:
            return []
        return scan_skills()

    def get_skill(self, name: str) -> SkillContent:
        if not config().skills.enabled:
            raise SkillNotFoundError("Skills are disabled.")
        return load_skill(name)

    def upsert_skill(self, *, name: str, description: str, body: str, category: str | None = None) -> SkillInfo:
        if not config().skills.enabled:
            raise SkillNotFoundError("Skills are disabled.")
        return save_skill(name=name, description=description, body=body, category=category)

    def list_skills_json(self) -> str:
        payload = [
            {
                "name": skill.name,
                "description": skill.description,
                "category": skill.category,
                "path": skill.relative_path,
            }
            for skill in self.list_skills()
        ]
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def view_skill_text(self, name: str) -> str:
        content = self.get_skill(name)
        return f"# Skill: {content.info.name}\n\n{content.body}"
