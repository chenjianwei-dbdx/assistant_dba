"""
Tests for Plugins
"""
import pytest
from backend.src.plugins.base import DBATool, ToolResult


class MockTool(DBATool):
    """测试用工具"""

    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing"

    @property
    def parameters(self):
        return [
            {"name": "param1", "type": "string", "required": True}
        ]

    def execute(self, **kwargs):
        return ToolResult(success=True, output={"result": kwargs.get("param1")})


def test_tool_result_creation():
    """测试 ToolResult 创建"""
    result = ToolResult(success=True, output={"key": "value"})
    assert result.success is True
    assert result.output == {"key": "value"}
    assert result.error is None


def test_tool_result_with_error():
    """测试 ToolResult 错误情况"""
    result = ToolResult(success=False, error="Test error")
    assert result.success is False
    assert result.error == "Test error"


def test_tool_schema():
    """测试工具 schema 生成"""
    tool = MockTool()
    schema = tool.get_schema()

    assert schema["name"] == "mock_tool"
    assert "parameters" in schema


def test_tool_execute():
    """测试工具执行"""
    tool = MockTool()
    result = tool.execute(param1="test_value")

    assert result.success is True
    assert result.output == "test_value"
