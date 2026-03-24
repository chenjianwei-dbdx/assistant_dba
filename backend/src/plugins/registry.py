"""
Plugin Registry Module
插件注册表
"""
from typing import Dict, List, Optional
from .base import DBATool


class PluginRegistry:
    """插件注册表"""

    def __init__(self):
        self._plugins: Dict[str, DBATool] = {}

    def register(self, plugin: DBATool) -> None:
        """注册插件"""
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> Optional[DBATool]:
        """获取插件"""
        return self._plugins.get(name)

    def list_all(self) -> List[DBATool]:
        """列出所有插件"""
        return list(self._plugins.values())

    def get_tools_prompt(self) -> str:
        """生成工具描述供 LLM 使用"""
        lines = []
        for plugin in self._plugins.values():
            params = [p["name"] for p in plugin.parameters]
            params_str = ", ".join(params) if params else "无"
            lines.append(f"- {plugin.name}({params_str}): {plugin.description}")
        return "\n".join(lines) if lines else "暂无可用工具"


# 全局注册表实例
_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """获取全局插件注册表"""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def register_plugin(plugin: DBATool) -> None:
    """注册插件（快捷函数）"""
    get_registry().register(plugin)
