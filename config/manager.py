"""Configuration management module."""

from pathlib import Path
from typing import Any, Optional
import os
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelSettings(BaseModel):
    """Model configuration settings."""
    primary: str = "deepseek"
    fallback: list[str] = Field(default_factory=lambda: ["zhipu", "qwen", "baidu", "openai", "anthropic"])


class MemoryFileSettings(BaseModel):
    """Memory file storage settings."""
    path: str = "~/.ai-agent/workspace"
    soul_md: str = "SOUL.md"
    memory_md: str = "MEMORY.md"
    heartbeat_md: str = "HEARTBEAT.md"


class MemoryDatabaseSettings(BaseModel):
    """Memory database settings."""
    type: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    name: str = "aiagent"
    user: str = "aiagent"
    password: str = ""


class MemorySettings(BaseModel):
    """Memory system settings."""
    file_store: MemoryFileSettings = Field(default_factory=MemoryFileSettings)
    database: MemoryDatabaseSettings = Field(default_factory=MemoryDatabaseSettings)


class SkillsSettings(BaseModel):
    """Skill system settings."""
    builtin_path: str = "./skills/builtin"
    extensions_path: str = "./skills/extensions"
    auto_update: bool = True
    default_skills: list[str] = Field(default_factory=lambda: ["file_manager", "web_browser", "code_helper"])


class WebSettings(BaseModel):
    """Web API settings."""
    port: int = 8080
    host: str = "0.0.0.0"
    websocket_enabled: bool = True


class GatewaySettings(BaseModel):
    """Gateway settings."""
    channels: list[str] = Field(default_factory=lambda: ["web"])
    web: WebSettings = Field(default_factory=WebSettings)
    internal_port: int = 18789


class HeartbeatSettings(BaseModel):
    """Heartbeat settings."""
    enabled: bool = True
    interval: int = 300


class LoggingSettings(BaseModel):
    """Logging settings."""
    level: str = "INFO"
    format: str = "json"
    file: str = "logs/ai-agent.log"


class Settings(BaseSettings):
    """Main application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )

    # Deployment
    deploy_mode: str = "local"
    version: str = "personal"

    # Model
    model: ModelSettings = Field(default_factory=ModelSettings)

    # Memory
    memory: MemorySettings = Field(default_factory=MemorySettings)

    # Skills
    skills: SkillsSettings = Field(default_factory=SkillsSettings)

    # Gateway
    gateway: GatewaySettings = Field(default_factory=GatewaySettings)

    # Heartbeat
    heartbeat: HeartbeatSettings = Field(default_factory=HeartbeatSettings)

    # Logging
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    # API Keys (from environment)
    deepseek_api_key: Optional[str] = None
    zhipu_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    baidu_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    @classmethod
    def from_yaml(cls, path: str = "config/settings.yaml") -> "Settings":
        """Load settings from YAML file with environment variable substitution."""
        config_path = Path(path)

        if not config_path.exists():
            return cls()

        with open(config_path, "r", encoding="utf-8") as f:
            yaml_content = f.read()

        # Substitute environment variables
        yaml_content = cls._substitute_env_vars(yaml_content)

        # Parse YAML
        config_dict = yaml.safe_load(yaml_content) or {}

        # Merge with environment variables
        return cls(**config_dict)

    @staticmethod
    def _substitute_env_vars(content: str) -> str:
        """Substitute ${VAR_NAME} with environment variable values."""
        import re

        pattern = r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}"

        def replace(match: re.Match) -> str:
            var_name = match.group(1)
            value = os.getenv(var_name, "")
            return value

        return re.sub(pattern, replace, content)

    def get_model_api_key(self, model_name: str) -> Optional[str]:
        """Get API key for a specific model."""
        key_mapping = {
            "deepseek": self.deepseek_api_key,
            "zhipu": self.zhipu_api_key,
            "qwen": self.qwen_api_key,
            "baidu": self.baidu_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }
        return key_mapping.get(model_name.lower())


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings

    if _settings is None:
        _settings = Settings.from_yaml()

    return _settings


def reload_settings(path: Optional[str] = None) -> Settings:
    """Reload settings from file."""
    global _settings

    if path:
        _settings = Settings.from_yaml(path)
    else:
        _settings = Settings.from_yaml()

    return _settings