"""
工具注册表模块
管理和注册所有可用工具
"""
from typing import Dict, List, Optional
from .base import BaseTool, ToolDefinition


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        注册工具

        Args:
            tool: 工具实例
        """
        name = tool.definition.name
        self._tools[name] = tool

    def register_function(self, func, definition: ToolDefinition) -> None:
        """
        注册函数为工具

        Args:
            func: 函数对象
            definition: 工具定义
        """
        tool = FunctionTool(func, definition)
        self._tools[definition.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例，如果不存在返回 None
        """
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """
        列出所有工具

        Returns:
            工具列表
        """
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())

    def get_definitions(self) -> List[ToolDefinition]:
        """获取所有工具定义"""
        return [tool.definition for tool in self._tools.values()]

    def get_definitions_for_prompt(self) -> str:
        """
        生成用于 prompt 的工具描述

        Returns:
            格式化的工具描述字符串
        """
        lines = []
        for tool in self._tools.values():
            d = tool.definition
            params = [p["name"] for p in d.parameters]
            params_str = ", ".join(params) if params else "无"
            lines.append(
                f"- {d.name}({params_str}): {d.description}"
            )
        return "\n".join(lines) if lines else "暂无可用工具"

    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()


class FunctionTool(BaseTool):
    """函数包装工具，将普通函数包装为工具"""

    def __init__(self, func, definition: ToolDefinition):
        self._func = func
        self._definition = definition

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    def execute(self, **kwargs) -> Dict:
        """执行包装的函数"""
        try:
            result = self._func(**kwargs)
            if isinstance(result, dict):
                return {"success": True, "output": result}
            return {"success": True, "output": str(result)}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局工具注册表实例
_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def set_registry(registry: ToolRegistry) -> None:
    """设置全局工具注册表"""
    global _global_registry
    _global_registry = registry
