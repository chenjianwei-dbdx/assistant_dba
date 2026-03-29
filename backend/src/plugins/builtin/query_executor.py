"""
Query Executor Plugin
SQL 查询执行插件
"""
import time
from typing import Dict, Any
from ..base import DBATool, ToolResult, PluginContext


class QueryExecutor(DBATool):
    """SQL 查询执行器"""

    @property
    def name(self) -> str:
        return "query_executor"

    @property
    def description(self) -> str:
        return "执行 SQL 查询语句并返回结果"

    @property
    def parameters(self) -> list:
        return [
            {
                "name": "connection_id",
                "type": "string",
                "required": False,
                "description": "数据库连接 ID（可选，默认使用监控数据库）"
            },
            {
                "name": "sql",
                "type": "string",
                "required": True,
                "description": "要执行的 SQL 语句"
            },
            {
                "name": "limit",
                "type": "integer",
                "required": False,
                "default": 1000,
                "description": "返回结果行数限制"
            }
        ]

    def execute(self, context: PluginContext, **kwargs) -> ToolResult:
        sql = kwargs.get("sql", "")
        limit = kwargs.get("limit", 1000)

        if not sql:
            return ToolResult(success=False, error="SQL 语句不能为空")

        # 简单危险操作检查
        dangerous_keywords = ['DROP', 'TRUNCATE', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'GRANT', 'REVOKE', 'ALTER']
        sql_upper = sql.strip().upper()
        if any(sql_upper.startswith(kw) or f' {kw} ' in sql_upper for kw in dangerous_keywords):
            return ToolResult(success=False, error=f"禁止执行危险 SQL: {sql[:50]}...")

        try:
            with context.get_connection() as conn:
                cur = conn.cursor()

                start_time = time.time()
                cur.execute(sql)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchmany(limit)
                execution_time_ms = int((time.time() - start_time) * 1000)

                cur.close()

                return ToolResult(
                    success=True,
                    output={
                        "columns": columns,
                        "rows": [dict(zip(columns, row)) for row in rows],
                        "row_count": len(rows),
                        "execution_time_ms": execution_time_ms
                    },
                    metadata={"sql": sql[:100], "limit": limit}
                )
        except Exception as e:
            return ToolResult(success=False, error=f"查询失败: {str(e)}")
