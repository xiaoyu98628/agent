from langchain_core.tools import BaseTool, tool

from app.application.skill.service import SkillService
from config.config import config


def build_skill_tools() -> list[BaseTool]:
    configure = config()
    if not configure.skills.enabled:
        return []

    service = SkillService()

    @tool
    def skills_list() -> str:
        """List available skills (name, description, category)."""
        return service.list_skills_json()

    @tool
    def skill_view(name: str) -> str:
        """Load full instructions for a skill by name."""
        try:
            return service.view_skill_text(name)
        except Exception as exc:
            return f"Error: {exc}"

    return [skills_list, skill_view]
