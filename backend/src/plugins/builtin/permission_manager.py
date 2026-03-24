"""
Permission Manager Plugin
权限管理插件
"""
from typing import Dict, List
from ..base import DBATool, ToolResult


class PermissionManager(DBATool):
    """数据库权限管理器"""

    @property
    def name(self) -> str:
        return "permission_manager"

    @property
    def description(self) -> str:
        return "管理数据库用户和权限"

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
                "required": True,
                "enum": ["list_users", "list_grants", "grant", "revoke"],
                "description": "操作类型"
            },
            {
                "name": "username",
                "type": "string",
                "required": False,
                "description": "用户名（grant/revoke 时需要）"
            },
            {
                "name": "privileges",
                "type": "string",
                "required": False,
                "description": "权限列表（如 SELECT,INSERT,UPDATE）"
            }
        ]

    def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "")
        connection_id = kwargs.get("connection_id", "")

        if action == "list_users":
            return self._list_users(connection_id)
        elif action == "list_grants":
            username = kwargs.get("username", "")
            return self._list_grants(connection_id, username)
        elif action == "grant":
            return self._grant(connection_id, kwargs.get("username", ""), kwargs.get("privileges", ""))
        elif action == "revoke":
            return self._revoke(connection_id, kwargs.get("username", ""), kwargs.get("privileges", ""))
        else:
            return ToolResult(success=False, error=f"Unknown action: {action}")

    def _list_users(self, connection_id: str) -> ToolResult:
        return ToolResult(
            success=True,
            output={
                "users": [
                    {"username": "admin", "host": "localhost", "privileges": ["ALL PRIVILEGES"]},
                    {"username": "app_user", "host": "%", "privileges": ["SELECT", "INSERT", "UPDATE"]},
                    {"username": "readonly", "host": "%", "privileges": ["SELECT"]}
                ]
            }
        )

    def _list_grants(self, connection_id: str, username: str) -> ToolResult:
        return ToolResult(
            success=True,
            output={
                "username": username,
                "grants": [
                    "SELECT ON *.* TO 'user'@'%'",
                    "INSERT ON *.* TO 'user'@'%'",
                    "UPDATE ON *.* TO 'user'@'%'"
                ]
            }
        )

    def _grant(self, connection_id: str, username: str, privileges: str) -> ToolResult:
        return ToolResult(
            success=True,
            output={
                "username": username,
                "privileges": privileges,
                "status": "granted"
            }
        )

    def _revoke(self, connection_id: str, username: str, privileges: str) -> ToolResult:
        return ToolResult(
            success=True,
            output={
                "username": username,
                "privileges": privileges,
                "status": "revoked"
            }
        )
