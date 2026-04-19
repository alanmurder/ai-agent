"""Skill Loader - Load skills from directories."""

import importlib.util
import os
from pathlib import Path
from typing import Any, Optional

import yaml

from skills.types import Skill, SkillConfig, SkillCategory, SkillVersion
from core.tools.types import Tool
from core.logging import get_logger

logger = get_logger("skills.loader")


class SkillLoader:
    """Load skills from directory structure."""

    @staticmethod
    async def load(skill_path: str) -> Optional[Skill]:
        """Load a skill from its directory."""
        path = Path(skill_path)

        if not path.exists():
            logger.warning("skill_path_not_found", path=skill_path)
            return None

        # Read SKILL.md
        skill_md_path = path / "SKILL.md"
        if not skill_md_path.exists():
            logger.warning("skill_md_not_found", path=skill_path)
            return None

        config = SkillLoader._parse_skill_md(skill_md_path)

        if not config:
            return None

        # Load tools
        tools = SkillLoader._load_tools(path)

        # Load prompts
        prompts = SkillLoader._load_prompts(path)

        # Load handlers
        handlers = SkillLoader._load_handlers(path)

        skill = Skill(
            config=config,
            tools=tools,
            prompts=prompts,
            handlers=handlers,
            path=str(path),
        )

        logger.info(
            "skill_loaded",
            name=config.name,
            tools=len(tools),
            path=skill_path,
        )

        return skill

    @staticmethod
    def _parse_skill_md(path: Path) -> Optional[SkillConfig]:
        """Parse SKILL.md file."""
        content = path.read_text(encoding="utf-8")

        # Extract frontmatter (YAML between ---)
        parts = content.split("---")
        if len(parts) < 3:
            logger.warning("invalid_skill_md_format", path=str(path))
            return None

        frontmatter = parts[1].strip()

        try:
            metadata = yaml.safe_load(frontmatter)
        except yaml.YAMLError as e:
            logger.error("skill_md_parse_error", path=str(path), error=str(e))
            return None

        # Parse category
        category_str = metadata.get("category", "system")
        try:
            category = SkillCategory(category_str.split("/")[-1])
        except ValueError:
            category = SkillCategory.SYSTEM

        # Parse compatible versions
        versions = metadata.get("compatible_versions", ["universal"])
        compatible_versions = []

        for v in versions:
            try:
                compatible_versions.append(SkillVersion(v.lower()))
            except ValueError:
                compatible_versions.append(SkillVersion.UNIVERSAL)

        config = SkillConfig(
            name=metadata.get("name", path.parent.name),
            version=metadata.get("version", "1.0.0"),
            category=category,
            compatible_versions=compatible_versions,
            description=metadata.get("description", ""),
            author=metadata.get("author", "unknown"),
            dependencies=metadata.get("dependencies", []),
            permissions=metadata.get("permissions", []),
            tags=metadata.get("tags", []),
            enabled=metadata.get("enabled", True),
            priority=metadata.get("priority", 100),
        )

        return config

    @staticmethod
    def _load_tools(path: Path) -> list[Tool]:
        """Load tools from tools.py."""
        tools_path = path / "tools.py"

        if not tools_path.exists():
            return []

        tools = []

        try:
            spec = importlib.util.spec_from_file_location("tools", tools_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for TOOL_DEFINITIONS list
            if hasattr(module, "TOOL_DEFINITIONS"):
                for tool_def in module.TOOL_DEFINITIONS:
                    tool = Tool(
                        name=tool_def.get("name", ""),
                        description=tool_def.get("description", ""),
                        parameters=tool_def.get("parameters", {}),
                        handler=tool_def.get("handler"),
                        permissions=tool_def.get("permissions", []),
                        timeout=tool_def.get("timeout", 30),
                    )
                    tools.append(tool)

        except Exception as e:
            logger.error("tools_load_error", path=str(path), error=str(e))

        return tools

    @staticmethod
    def _load_prompts(path: Path) -> dict[str, str]:
        """Load prompts from prompts.py."""
        prompts_path = path / "prompts.py"

        if not prompts_path.exists():
            return {}

        prompts = {}

        try:
            spec = importlib.util.spec_from_file_location("prompts", prompts_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for PROMPTS dict
            if hasattr(module, "PROMPTS"):
                prompts = module.PROMPTS

        except Exception as e:
            logger.error("prompts_load_error", path=str(path), error=str(e))

        return prompts

    @staticmethod
    def _load_handlers(path: Path) -> dict[str, Any]:
        """Load handlers from handlers.py."""
        handlers_path = path / "handlers.py"

        if not handlers_path.exists():
            return {}

        handlers = {}

        try:
            spec = importlib.util.spec_from_file_location("handlers", handlers_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get all handler functions (functions starting with handle_)
            for name in dir(module):
                if name.startswith("handle_"):
                    handlers[name] = getattr(module, name)

        except Exception as e:
            logger.error("handlers_load_error", path=str(path), error=str(e))

        return handlers

    @staticmethod
    def discover_skills(base_path: str, category: Optional[str] = None) -> list[str]:
        """Discover skill directories."""
        path = Path(base_path)

        if not path.exists():
            return []

        skill_paths = []

        for item in path.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                # Filter by category if specified
                if category:
                    skill_md = item / "SKILL.md"
                    content = skill_md.read_text(encoding="utf-8")
                    if category not in content:
                        continue

                skill_paths.append(str(item))

        return skill_paths