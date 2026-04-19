"""Tool Registry - Register and manage available tools."""

from typing import Any, Dict, Optional
import importlib

from core.tools.types import Tool, ToolDefinition
from core.logging import get_logger

logger = get_logger("tools.registry")


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self._handlers: Dict[str, Any] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info("tool_registered", tool=tool.name)

    def unregister(self, tool_name: str) -> bool:
        """Unregister a tool."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._handlers[tool_name]
            logger.info("tool_unregistered", tool=tool_name)
            return True
        return False

    def get(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def get_all(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return self._tools.copy()

    def get_tool_names(self) -> list[str]:
        """Get list of all tool names."""
        return list(self._tools.keys())

    def register_handler(self, tool_name: str, handler: Any) -> None:
        """Register a handler for a tool."""
        if tool_name in self._tools:
            self._handlers[tool_name] = handler
            logger.info("handler_registered", tool=tool_name)

    def get_handler(self, tool_name: str) -> Optional[Any]:
        """Get handler for a tool."""
        return self._handlers.get(tool_name)

    def load_handler_from_path(self, tool_name: str, handler_path: str) -> None:
        """Load handler from module path."""
        parts = handler_path.split(":")
        module_path = parts[0]
        function_name = parts[1] if len(parts) > 1 else "handle"

        try:
            module = importlib.import_module(module_path)
            handler = getattr(module, function_name)
            self.register_handler(tool_name, handler)

        except Exception as e:
            logger.error("handler_load_failed", tool=tool_name, error=str(e))

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Convert all tools to OpenAI format."""
        tools = []
        for tool in self._tools.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        return tools

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._handlers.clear()


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get or create global tool registry."""
    global _registry

    if _registry is None:
        _registry = ToolRegistry()

    return _registry


def register_tool(tool: Tool) -> None:
    """Register a tool in the global registry."""
    get_registry().register(tool)