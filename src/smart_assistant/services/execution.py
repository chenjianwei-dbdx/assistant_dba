"""
工具执行服务模块
"""
import time
from typing import Dict, Any
from ..tools.registry import ToolRegistry


class ExecutionService:
    """工具执行服务"""

    def __init__(self, tool_registry: ToolRegistry):
        """
        初始化执行服务

        Args:
            tool_registry: 工具注册表
        """
        self.tool_registry = tool_registry

    def execute(self, tool_name: str, params: Dict) -> Dict[str, Any]:
        """
        执行工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            执行结果
        """
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
                "tool_name": tool_name
            }

        # 验证参数
        is_valid, missing, invalid = tool.validate_params(**params)
        if not is_valid:
            if missing:
                return {
                    "success": False,
                    "error": f"Missing required parameters: {missing}",
                    "tool_name": tool_name,
                    "missing_params": missing
                }
            if invalid:
                return {
                    "success": False,
                    "error": f"Invalid parameters: {invalid}",
                    "tool_name": tool_name
                }

        # 执行工具
        start_time = time.time()
        try:
            result = tool.execute(**params)
            execution_time = int((time.time() - start_time) * 1000)

            return {
                "success": result.get("success", False),
                "output": result.get("output", result.get("stdout", "")),
                "error": result.get("error", result.get("stderr", "")),
                "tool_name": tool_name,
                "execution_time_ms": execution_time,
                "returncode": result.get("returncode")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "tool_name": tool_name,
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }

    def validate_tool_exists(self, tool_name: str) -> bool:
        """
        验证工具是否存在

        Args:
            tool_name: 工具名称

        Returns:
            是否存在
        """
        return self.tool_registry.get_tool(tool_name) is not None

    def list_available_tools(self) -> list:
        """
        列出所有可用工具

        Returns:
            工具信息列表
        """
        tools = self.tool_registry.list_tools()
        return [
            {
                "name": tool.definition.name,
                "description": tool.definition.description,
                "category": tool.definition.category,
                "parameters": tool.definition.parameters
            }
            for tool in tools
        ]
