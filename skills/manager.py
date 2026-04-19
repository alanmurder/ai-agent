"""Skill Manager - Manage loaded skills."""

from typing import Any, Optional
from pathlib import Path

from skills.loader import SkillLoader
from skills.types import Skill, SkillConfig, SkillCategory, SkillVersion
from core.tools.registry import ToolRegistry, get_registry
from core.logging import get_logger, log_skill_usage
from core.metrics import get_metrics, MetricNames
from config import get_settings

logger = get_logger("skills.manager")
metrics = get_metrics()


class SkillManager:
    """Manage skills lifecycle."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._builtin_skills: dict[str, Skill] = {}
        self._extension_skills: dict[str, Skill] = {}
        self._skill_registry: dict[str, Skill] = {}
        self._tool_registry: ToolRegistry = get_registry()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize and load builtin skills."""
        builtin_path = self.settings.skills.builtin_path

        # Load personal skills
        personal_path = Path(builtin_path) / "personal"
        if personal_path.exists():
            await self._load_skills_from_dir(personal_path, "builtin")

        # Load enterprise skills if version is enterprise
        if self.settings.version == "enterprise":
            enterprise_path = Path(builtin_path) / "enterprise"
            if enterprise_path.exists():
                await self._load_skills_from_dir(enterprise_path, "builtin")

        # Load extension skills
        extensions_path = self.settings.skills.extensions_path
        if Path(extensions_path).exists():
            await self._load_skills_from_dir(extensions_path, "extension")

        self._initialized = True

        logger.info(
            "skill_manager_initialized",
            builtin=len(self._builtin_skills),
            extensions=len(self._extension_skills),
        )

    async def _load_skills_from_dir(
        self,
        path: Path,
        skill_type: str,
    ) -> None:
        """Load all skills from a directory."""
        skill_paths = SkillLoader.discover_skills(str(path))

        for skill_path in skill_paths:
            skill = await SkillLoader.load(skill_path)

            if skill:
                if skill_type == "builtin":
                    self._builtin_skills[skill.name] = skill
                else:
                    self._extension_skills[skill.name] = skill

                self._skill_registry[skill.name] = skill

                # Register tools
                for tool in skill.tools:
                    self._tool_registry.register(tool)

                    # Register handler if available
                    if tool.handler:
                        handler_name = f"handle_{tool.name}"
                        if handler_name in skill.handlers:
                            self._tool_registry.register_handler(
                                tool.name,
                                skill.handlers[handler_name],
                            )

                metrics.increment(MetricNames.SKILL_LOAD_COUNT)

    async def discover_skills(
        self,
        category: Optional[str] = None,
    ) -> list[Skill]:
        """Discover available skills."""
        if not self._initialized:
            await self.initialize()

        skills = []

        for skill in self._skill_registry.values():
            if category:
                if skill.category.value != category:
                    continue

            skills.append(skill)

        # Sort by priority
        skills.sort(key=lambda s: s.config.priority)

        return skills

    async def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a specific skill by name."""
        return self._skill_registry.get(skill_name)

    async def get_active_skills(self, user_id: str) -> list[str]:
        """Get list of active skill names for a user."""
        if not self._initialized:
            await self.initialize()

        # Return default skills for MVP
        default_skills = self.settings.skills.default_skills

        active = []

        for skill_name in default_skills:
            if skill_name in self._skill_registry:
                active.append(skill_name)

        return active

    def get_tool_names(self, skill_names: list[str]) -> list[str]:
        """Get tool names for given skills."""
        tools = []

        for skill_name in skill_names:
            skill = self._skill_registry.get(skill_name)

            if skill:
                for tool in skill.tools:
                    tools.append(tool.name)

        return tools

    def get_skill_tools(self, skill_name: str) -> list[Any]:
        """Get tool definitions for a skill."""
        skill = self._skill_registry.get(skill_name)

        if skill:
            return skill.tools

        return []

    async def reload_skill(self, skill_name: str) -> bool:
        """Reload a skill from disk."""
        skill = self._skill_registry.get(skill_name)

        if not skill:
            return False

        new_skill = await SkillLoader.load(skill.path)

        if new_skill:
            # Update registry
            self._skill_registry[skill_name] = new_skill

            # Re-register tools
            for tool in new_skill.tools:
                self._tool_registry.register(tool)

            logger.info("skill_reloaded", name=skill_name)

            return True

        return False

    async def enable_skill(self, skill_name: str) -> bool:
        """Enable a skill."""
        skill = self._skill_registry.get(skill_name)

        if skill:
            skill.config.enabled = True

            log_skill_usage(
                logger,
                skill_name=skill_name,
                user_id="system",
                action="enable",
                success=True,
            )

            return True

        return False

    async def disable_skill(self, skill_name: str) -> bool:
        """Disable a skill."""
        skill = self._skill_registry.get(skill_name)

        if skill:
            skill.config.enabled = False

            log_skill_usage(
                logger,
                skill_name=skill_name,
                user_id="system",
                action="disable",
                success=True,
            )

            return True

        return False

    def get_skill_count(self) -> int:
        """Get total number of loaded skills."""
        return len(self._skill_registry)