"""
Slow Query Analyzer Plugin
慢查询分析插件
"""
from typing import Dict
from ..base import DBATool, ToolResult
from src.db.connection import get_monitor_connection


class SlowQueryAnalyzer(DBATool):
    """慢查询分析器"""

    @property
    def name(self) -> str:
        return "slow_query_analyzer"

    @property
    def description(self) -> str:
        return "分析最近的慢查询，提供优化建议"

    @property
    def parameters(self) -> list:
        return [
            {
                "name": "connection_id",
                "type": "string",
                "required": False,
                "description": "数据库连接 ID（可选）"
            },
            {
                "name": "limit",
                "type": "integer",
                "required": False,
                "default": 10,
                "description": "返回的慢查询数量"
            },
            {
                "name": "threshold_ms",
                "type": "integer",
                "required": False,
                "default": 100,
                "description": "慢查询阈值（毫秒）"
            }
        ]

    def execute(self, **kwargs) -> ToolResult:
        limit = kwargs.get("limit", 10)
        threshold_ms = kwargs.get("threshold_ms", 100)

        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            # 查询慢查询（需要 pg_stat_statements 扩展）
            cur.execute("""
                SELECT query, calls, total_exec_time, mean_exec_time, max_exec_time, min_exec_time
                FROM pg_stat_statements
                WHERE mean_exec_time >= %s
                ORDER BY mean_exec_time DESC
                LIMIT %s
            """, (threshold_ms, limit))

            slow_queries = []
            for row in cur.fetchall():
                sql = row[0]
                # 生成简单建议
                suggestions = self._generate_suggestions(sql, row[3])

                slow_queries.append({
                    "sql": sql,
                    "calls": row[1],
                    "total_time_ms": round(row[2], 2),
                    "mean_time_ms": round(row[3], 2),
                    "max_time_ms": round(row[4], 2),
                    "min_time_ms": round(row[5], 2),
                    "suggestions": suggestions
                })

            cur.close()
            conn.close()

            if not slow_queries:
                return ToolResult(
                    success=True,
                    output={
                        "slow_queries": [],
                        "total_count": 0,
                        "message": "未发现慢查询或 pg_stat_statements 未启用"
                    }
                )

            return ToolResult(
                success=True,
                output={
                    "slow_queries": slow_queries,
                    "total_count": len(slow_queries)
                },
                metadata={"limit": limit, "threshold_ms": threshold_ms}
            )
        except Exception as e:
            error_msg = str(e)
            if "pg_stat_statements" in error_msg.lower() or "undefined table" in error_msg.lower():
                return ToolResult(
                    success=False,
                    error="pg_stat_statements 扩展未启用，请联系 DBA 执行: CREATE EXTENSION pg_stat_statements"
                )
            return ToolResult(success=False, error=f"分析慢查询失败: {error_msg}")

    def _generate_suggestions(self, sql: str, mean_time_ms: float) -> list:
        """根据 SQL 和执行时间生成优化建议"""
        suggestions = []
        sql_upper = sql.upper()

        if "SELECT *" in sql_upper:
            suggestions.append("避免使用 SELECT *，只查询需要的列")

        if "WHERE" not in sql_upper and "LIMIT" not in sql_upper:
            suggestions.append("建议添加 WHERE 条件限制返回行数")

        if not sql_upper.strip().startswith("SELECT"):
            suggestions.append("建议检查是否为只读查询")

        if mean_time_ms > 1000:
            suggestions.append("执行时间过长，考虑优化查询或添加索引")

        if "JOIN" in sql_upper:
            suggestions.append("检查 JOIN 条件是否使用了索引列")

        if "LIKE" in sql_upper and "%" in sql:
            suggestions.append("LIKE 条件尽量避免前导通配符")

        if not suggestions:
            suggestions.append("建议使用 EXPLAIN ANALYZE 分析具体执行计划")

        return suggestions
