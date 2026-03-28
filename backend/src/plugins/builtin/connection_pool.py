"""
Connection Pool Monitor Plugin
连接池监控插件
"""
import psycopg2
from typing import Dict, List
from ..base import DBATool, ToolResult
from src.db.connection import get_monitor_connection


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
                "required": False,
                "description": "数据库连接 ID（可选）"
            },
            {
                "name": "action",
                "type": "string",
                "required": False,
                "enum": ["status", "list", "kill", "variables"],
                "description": "操作类型"
            },
            {
                "name": "pid",
                "type": "integer",
                "required": False,
                "description": "进程 ID（kill 时需要）"
            }
        ]

    def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "status")

        if action == "status":
            return self._pool_status()
        elif action == "list":
            return self._list_connections()
        elif action == "variables":
            return self._pool_variables()
        elif action == "kill":
            pid = kwargs.get("pid")
            if not pid:
                return ToolResult(success=False, error="pid 不能为空")
            return self._kill_connection(pid)
        else:
            return ToolResult(success=False, error=f"Unknown action: {action}")

    def _pool_status(self) -> ToolResult:
        """获取连接池状态"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            # 获取总连接数
            cur.execute("SELECT COUNT(*) FROM pg_stat_activity")
            total = cur.fetchone()[0]

            # 获取活跃连接数
            cur.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'")
            active = cur.fetchone()[0]

            # 获取空闲连接数
            cur.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'idle'")
            idle = cur.fetchone()[0]

            # 获取等待中的连接
            cur.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE wait_event IS NOT NULL")
            waiting = cur.fetchone()[0]

            # 获取最大连接数
            cur.execute("SHOW max_connections")
            max_conn = cur.fetchone()[0]

            cur.close()
            conn.close()

            return ToolResult(
                success=True,
                output={
                    "max_connections": int(max_conn),
                    "total": total,
                    "active": active,
                    "idle": idle,
                    "waiting": waiting,
                    "available": int(max_conn) - total
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"获取连接池状态失败: {str(e)}")

    def _list_connections(self) -> ToolResult:
        """列出所有连接"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT pid, usename, application_name, client_addr, state, query_start, wait_event
                FROM pg_stat_activity
                WHERE datname = (SELECT datname FROM pg_stat_activity WHERE pid = pg_backend_pid())
                ORDER BY query_start
            """)

            connections = []
            for row in cur.fetchall():
                connections.append({
                    "pid": row[0],
                    "username": row[1],
                    "application": row[2] or "psql",
                    "client_addr": str(row[3]) if row[3] else "local",
                    "state": row[4] or "unknown",
                    "query_start": str(row[5]) if row[5] else None,
                    "wait_event": row[6]
                })

            cur.close()
            conn.close()

            return ToolResult(success=True, output={"connections": connections})
        except Exception as e:
            return ToolResult(success=False, error=f"列出连接失败: {str(e)}")

    def _pool_variables(self) -> ToolResult:
        """获取连接池变量"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT name, setting, unit FROM pg_settings
                WHERE name IN ('max_connections', 'shared_buffers', 'effective_cache_size',
                               'work_mem', 'maintenance_work_mem', 'max_wal_size')
            """)

            variables = []
            for row in cur.fetchall():
                variables.append({
                    "name": row[0],
                    "value": row[1] + (row[2] or ""),
                })

            cur.close()
            conn.close()

            return ToolResult(success=True, output={"variables": variables})
        except Exception as e:
            return ToolResult(success=False, error=f"获取变量失败: {str(e)}")

    def _kill_connection(self, pid: int) -> ToolResult:
        """终止连接"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()
            cur.execute("SELECT pg_terminate_backend(%s)", (pid,))
            conn.commit()

            cur.close()
            conn.close()

            return ToolResult(success=True, output={"pid": pid, "killed": True})
        except Exception as e:
            return ToolResult(success=False, error=f"终止连接失败: {str(e)}")
