# core/tool/registry.py
from typing import Dict
from .base import BaseTool

class ToolRegistry:
    def __init__(self):
        # 1. 这里定义了下划线版本
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool):
        # 2. 这里也要用下划线
        self._tools[tool.name] = tool

    def get_tool_manifest(self) -> str:
        # 3. 💡 报错就在这里，请加上下划线！
        # 顺便加了空格，让模型读得更清楚
        return "\n".join([f"- {t.name}: {t.description}" for t in self._tools.values()])

    def execute(self, name: str, params: str) -> str:
        # 4. 这里也要用下划线
        if name not in self._tools:
            return f"Error: Tool {name} not found."
        return self._tools[name].run(params)