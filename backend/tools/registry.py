from typing import Dict, List

from .base import Tool


class ToolRegistry:
    """Holds every tool by name. Registering a new Tool subclass is all it takes to plug one in."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> Tool:
        if not tool.name or not tool.category:
            raise ValueError("Tool needs a name and a category")
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Unknown tool '{name}'")
        return self._tools[name]

    def by_category(self, category: str) -> List[Tool]:
        """Tools in a category, in fallback order (lowest priority number first)."""
        tools = [t for t in self._tools.values() if t.category == category]
        return sorted(tools, key=lambda t: t.priority)

    def categories(self) -> List[str]:
        return sorted({t.category for t in self._tools.values()})

    def all(self) -> List[Tool]:
        return list(self._tools.values())

    def __len__(self) -> int:
        return len(self._tools)
