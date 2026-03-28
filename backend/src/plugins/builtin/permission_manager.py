"""
Permission Manager Plugin
权限管理插件
"""
from typing import Dict, List
from ..base import DBATool, ToolResult
from src.db.connection import get_monitor_connection


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
                "required": False,
                "description": "数据库连接 ID（可选）"
            },
            {
                "name": "action",
                "type": "string",
                "required": True,
                "enum": ["list_users", "list_grants", "list_roles", "show_grants"],
                "description": "操作类型"
            },
            {
                "name": "username",
                "type": "string",
                "required": False,
                "description": "用户名（list_grants/show_grants 时需要）"
            }
        ]

    def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "")
        username = kwargs.get("username", "")

        if action == "list_users":
            return self._list_users()
        elif action == "list_grants":
            return self._list_grants(username)
        elif action == "list_roles":
            return self._list_roles()
        elif action == "show_grants":
            if not username:
                return ToolResult(success=False, error="username 不能为空")
            return self._show_grants(username)
        else:
            return ToolResult(success=False, error=f"Unknown action: {action}")

    def _list_users(self) -> ToolResult:
        """列出所有数据库用户"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT usename, usesuper, usecreatedb, valuntil
                FROM pg_user
                ORDER BY usename
            """)

            users = []
            for row in cur.fetchall():
                users.append({
                    "username": row[0],
                    "is_superuser": row[1],
                    "can_create_db": row[2],
                    "expire_time": str(row[3]) if row[3] else "never"
                })

            cur.close()
            conn.close()

            return ToolResult(success=True, output={"users": users})
        except Exception as e:
            return ToolResult(success=False, error=f"列出用户失败: {str(e)}")

    def _list_roles(self) -> ToolResult:
        """列出所有角色"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolreplication
                FROM pg_roles
                ORDER BY rolname
            """)

            roles = []
            for row in cur.fetchall():
                roles.append({
                    "role": row[0],
                    "is_super": row[1],
                    "can_create_db": row[2],
                    "can_create_role": row[3],
                    "is_replication": row[4]
                })

            cur.close()
            conn.close()

            return ToolResult(success=True, output={"roles": roles})
        except Exception as e:
            return ToolResult(success=False, error=f"列出角色失败: {str(e)}")

    def _list_grants(self, username: str) -> ToolResult:
        """列出用户的权限（数据库级别）"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT DISTINCT
                    c.relname,
                    c.relkind,
                    CASE c.relkind WHEN 'r' THEN 'table' WHEN 'v' THEN 'view' WHEN 'm' THEN 'materialized view' WHEN 'S' THEN 'sequence' END as object_type,
                    privilege_type
                FROM information_schema.table_privileges g
                JOIN information_schema.tables t ON g.table_name = t.table_name AND g.table_schema = t.table_schema
                JOIN pg_class c ON c.relname = t.table_name AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = t.table_schema)
                WHERE grantee = %s
                ORDER BY c.relname, privilege_type
            """, (username,))

            grants = []
            for row in cur.fetchall():
                grants.append({
                    "object": row[0],
                    "object_type": row[2],
                    "privilege": row[3]
                })

            cur.close()
            conn.close()

            return ToolResult(success=True, output={"username": username, "grants": grants})
        except Exception as e:
            return ToolResult(success=False, error=f"列出权限失败: {str(e)}")

    def _show_grants(self, username: str) -> ToolResult:
        """显示用户的详细权限"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            # 获取用户基本信息
            cur.execute("""
                SELECT usename, usesuper, usecreatedb
                FROM pg_user WHERE usename = %s
            """, (username,))

            user_row = cur.fetchone()
            if not user_row:
                cur.close()
                conn.close()
                return ToolResult(success=False, error=f"用户 {username} 不存在")

            # 获取角色成员关系
            cur.execute("""
                SELECT r.rolname
                FROM pg_auth_members m
                JOIN pg_roles r ON m.roleid = r.oid
                JOIN pg_auth_members m2 ON m.member = m2.member
                JOIN pg_roles r2 ON m2.roleid = r2.oid
                WHERE r2.rolname = %s
            """, (username,))

            roles = [row[0] for row in cur.fetchall()]

            # 获取表权限
            cur.execute("""
                SELECT c.relname, privilege_type
                FROM information_schema.table_privileges g
                JOIN pg_class c ON c.relname = g.table_name
                WHERE grantee = %s
            """, (username,))

            table_privs = {}
            for row in cur.fetchall():
                if row[0] not in table_privs:
                    table_privs[row[0]] = []
                table_privs[row[0]].append(row[1])

            # 获取列权限
            cur.execute("""
                SELECT c.relname, a.attname, privilege_type
                FROM information_schema.column_privileges g
                JOIN pg_class c ON c.relname = g.table_name
                JOIN pg_attribute a ON a.attname = g.column_name AND a.attrelid = c.oid
                WHERE grantee = %s
            """, (username,))

            column_privs = {}
            for row in cur.fetchall():
                key = f"{row[0]}.{row[1]}"
                if key not in column_privs:
                    column_privs[key] = []
                column_privs[key].append(row[2])

            cur.close()
            conn.close()

            return ToolResult(success=True, output={
                "username": username,
                "is_superuser": user_row[1],
                "can_create_db": user_row[2],
                "roles": roles,
                "table_privileges": table_privs,
                "column_privileges": column_privs
            })
        except Exception as e:
            return ToolResult(success=False, error=f"显示权限失败: {str(e)}")
