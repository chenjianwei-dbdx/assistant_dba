"""
Plugin Base Module
插件基类
"""
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Dict, Any


class PluginContext:
    """插件执行上下文，提供插件所需的服务"""

    def __init__(self, db_manager, llm_client, config: dict):
        self.db_manager = db_manager
        self.llm_client = llm_client
        self.config = config

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = self.db_manager.get_raw_connection()
        try:
            yield conn
        finally:
            conn.close()


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
    def execute(self, context: PluginContext, **kwargs) -> ToolResult:
        """使用 PluginContext 执行工具"""
        pass

    def get_schema(self) -> Dict:
        """获取参数 schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
