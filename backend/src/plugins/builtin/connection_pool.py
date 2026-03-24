"""
Connection Pool Monitor Plugin
连接池监控插件
"""
from typing import Dict, List
from ..base import DBATool, ToolResult


class ConnectionPoolMonitor(DBATool):
    """数据库连接池监控"""

    @property
    def name(self) -> str:
        return "connection_pool_monitor"

    @property
    def description(self) -> str:
        return "监控数据库连接池状态、连接使用情况"

    @property
    def parameters(self) -> List[Dict]:
        return [
            {
                "name": "connection_id",
                "type": "string",
                "required": True,
                "description": "数据库连接 ID"
            },
            {
                "name": "action",
                "type": "string",
                "required": False,
                "enum": ["status", "kill", "variables"],
                "description": "操作类型"
            },
            {
                "name": "process_id",
                "type": "integer",
                "required": False,
                "description": "进程 ID（kill 时需要）"
            }
        ]

    def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "status")
        connection_id = kwargs.get("connection_id", "")

        if action == "status":
            return self._pool_status(connection_id)
        elif action == "variables":
            return self._pool_variables(connection_id)
        elif action == "kill":
            process_id = kwargs.get("process_id")
            if not process_id:
                return ToolResult(success=False, error="process_id 不能为空")
            return self._kill_connection(connection_id, process_id)
        else:
            return ToolResult(success=False, error=f"Unknown action: {action}")

    def _pool_status(self, connection_id: str) -> ToolResult:
        return ToolResult(
            success=True,
            output={
                "max_connections": 100,
                "active": 23,
                "idle": 77,
                "threads_connected": 23,
                "threads_running": 5,
                "connections_per_second": 1.5
            }
        )

    def _pool_variables(self, connection_id: str) -> ToolResult:
        return ToolResult(
            success=True,
            output={
                "variables": [
                    {"name": "max_connections", "value": "100"},
                    {"name": "wait_timeout", "value": "28800"},
                    {"name": "innodb_buffer_pool_size", "value": "134217728"}
                ]
            }
        )

    def _kill_connection(self, connection_id: str, process_id: int) -> ToolResult:
        return ToolResult(
            success=True,
            output={
                "process_id": process_id,
                "killed": True
            }
        )
