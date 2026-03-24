"""
Plugin Base Module
插件基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class ToolResult:
    """工具执行结果"""

    def __init__(
        self,
        success: bool,
        output: Any = None,
        error: str | None = None,
        metadata: Dict | None = None
    ):
        self.success = success
        self.output = output
        self.error = error
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata
        }


class DBATool(ABC):
    """DBA 工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    def parameters(self) -> list:
        """参数定义"""
        return []

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    def get_schema(self) -> Dict:
        """获取参数 schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
