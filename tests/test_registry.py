"""
Tests for Plugin Registry
"""
import pytest
from backend.src.plugins.registry import PluginRegistry, DBATool
from backend.src.plugins.base import ToolResult


class DummyTool(DBATool):
    @property
    def name(self) -> str:
        return "dummy_tool"

    @property
    def description(self) -> str:
        return "A dummy tool"

    @property
    def parameters(self):
        return []

    def execute(self, **kwargs):
        return ToolResult(success=True, output="done")


def test_registry_singleton():
    """测试注册表单例"""
    from backend.src.plugins.registry import get_registry
    reg1 = get_registry()
    reg2 = get_registry()
    assert reg1 is reg2


def test_registry_register_and_get():
    """测试注册和获取工具"""
    registry = PluginRegistry()
    tool = DummyTool()

    registry.register(tool)
    assert registry.get("dummy_tool") is tool


def test_registry_list_all():
    """测试列出所有工具"""
    registry = PluginRegistry()
    tool = DummyTool()
    registry.register(tool)

    tools = registry.list_all()
    assert len(tools) > 0
    assert any(t.name == "dummy_tool" for t in tools)


def test_registry_get_tools_prompt():
    """测试生成工具提示文本"""
    registry = PluginRegistry()
    tool = DummyTool()
    registry.register(tool)

    prompt = registry.get_tools_prompt()
    assert "dummy_tool" in prompt
    assert "A dummy tool" in prompt
