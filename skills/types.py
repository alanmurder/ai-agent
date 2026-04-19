"""Skill system types."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class SkillCategory(Enum):
    """Skill category classification."""
    LIFESTYLE = "lifestyle"
    LEARNING = "learning"
    WORK = "work"
    CODING = "coding"
    ECOMMERCE = "ecommerce"
    SYSTEM = "system"
    COMMUNICATION = "communication"


class SkillVersion(Enum):
    """Skill version compatibility."""
    PERSONAL = "personal"
    ENTERPRISE = "enterprise"
    UNIVERSAL = "universal"


@dataclass
class SkillConfig:
    """Skill configuration."""
    name: str
    version: str = "1.0.0"
    category: SkillCategory = SkillCategory.SYSTEM
    compatible_versions: list[SkillVersion] = field(default_factory=lambda: [SkillVersion.UNIVERSAL])
    description: str = ""
    author: str = "builtin"
    dependencies: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 100  # Higher priority = executed first


@dataclass
class Skill:
    """Loaded skill instance."""
    config: SkillConfig
    tools: list[Any] = field(default_factory=list)  # List of Tool objects
    prompts: dict[str, str] = field(default_factory=dict)
    handlers: dict[str, Any] = field(default_factory=dict)
    path: str = ""
    loaded_at: datetime = field(default_factory=datetime.now)

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def category(self) -> SkillCategory:
        return self.config.category


@dataclass
class SkillDraft:
    """Draft skill for creation."""
    name: str
    skill_md: str
    tools: str  # Python code
    handlers: str  # Python code
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillFeedback:
    """Feedback for skill optimization."""
    skill_name: str
    slow_execution: bool = False
    low_accuracy: bool = False
    user_suggestions: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)