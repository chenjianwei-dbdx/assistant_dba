"""
Query Executor Plugin
SQL 查询执行插件
"""
import re
import time
from typing import Dict, Any, Tuple
from ..base import DBATool, ToolResult, PluginContext


# SQL 安全白名单 - 只允许这些操作
ALLOWED_OPERATIONS = {"SELECT", "WITH"}
# 危险关键字黑名单
DANGEROUS_KEYWORDS = {
    "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE",
    "GRANT", "REVOKE", "EXECUTE", "COPY", "PG_READ", "PG_WRITE"
}


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

        # 验证 SQL 安全性
        is_safe, error_msg = self._validate_sql(sql)
        if not is_safe:
            return ToolResult(success=False, error=f"SQL 安全验证失败: {error_msg}")

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

    def _validate_sql(self, sql: str) -> Tuple[bool, str]:
        """
        验证 SQL 安全性

        Returns:
            (is_safe, error_message)
        """
        if not sql:
            return False, "SQL 为空"

        sql_upper = sql.upper()

        # 检查是否以允许的操作开头
        sql_stripped = sql_upper.strip()
        starts_with_allowed = any(
            sql_stripped.startswith(op) for op in ALLOWED_OPERATIONS
        )
        if not starts_with_allowed:
            return False, f"只允许以 {ALLOWED_OPERATIONS} 开头的查询"

        # 检查危险关键字
        for keyword in DANGEROUS_KEYWORDS:
            # 精确匹配，避免误报
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"禁止使用 {keyword} 操作"

        # 检查常见的注入模式
        injection_patterns = [
            r";\s*\w",  # 分号后跟命令
            r"--",  # SQL 注释
            r"/\*.*\*/",  # 块注释
            r"'\s*;\s*'",  # 空字符串注入
            r"pg_read_file",  # 文件读取
            r"pg_execute_server_program",  # 服务端程序执行
        ]

        for pattern in injection_patterns:
            if re.search(pattern, sql_upper):
                return False, f"检测到可疑的 SQL 模式"

        return True, ""

    def format_results(self, results: Dict[str, Any]) -> str:
        """格式化查询结果为可读文本"""
        if not results.get("success", False):
            return f"查询失败: {results.get('error', '未知错误')}"

        output = results.get("output", {})
        rows = output.get("rows", [])
        columns = output.get("columns", [])

        if not rows:
            return "查询成功，但没有返回任何结果。"

        lines = []
        lines.append(f"查询成功，返回 {output.get('row_count', 0)} 行:\n")

        # 构建表格
        col_widths = [len(c) for c in columns]
        for row in rows:
            for i, val in enumerate(row.values() if isinstance(row, dict) else row):
                val_str = str(val) if val is not None else "NULL"
                col_widths[i] = max(col_widths[i], min(len(val_str), 50))

        # 表头
        header = " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(columns))
        separator = "-|-".join("-" * w for w in col_widths)
        lines.append(header)
        lines.append(separator)

        # 数据行
        for row in rows[:20]:  # 最多显示 20 行
            if isinstance(row, dict):
                vals = [str(v) if v is not None else "NULL" for v in row.values()]
            else:
                vals = [str(v) if v is not None else "NULL" for v in row]
            row_str = " | ".join(
                val.ljust(col_widths[i]) for i, val in enumerate(vals)
            )
            lines.append(row_str)

        if output.get("row_count", 0) > 20:
            lines.append(f"\n... (结果被截断，仅显示前 20 行)")

        return "\n".join(lines)
