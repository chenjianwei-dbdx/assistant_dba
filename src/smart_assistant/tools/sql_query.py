"""
SQL Query Tool
自然语言转 SQL 工具，支持安全执行 PostgreSQL 查询
"""
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .base import BaseTool, ToolDefinition
from ..db.schema_introspector import SchemaIntrospector
from ..llm.client import LLMClient


# SQL 安全白名单 - 只允许这些操作
ALLOWED_OPERATIONS = {"SELECT", "WITH"}
# 危险关键字黑名单
DANGEROUS_KEYWORDS = {
    "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE",
    "GRANT", "REVOKE", "EXECUTE", "COPY", "PG_READ", "PG_WRITE"
}


@dataclass
class SQLResult:
    """SQL 执行结果"""
    success: bool
    rows: List[tuple]
    columns: List[str]
    row_count: int
    execution_time_ms: float
    error: Optional[str] = None


class SQLQueryTool(BaseTool):
    """自然语言转 SQL 查询工具"""

    def __init__(
        self,
        llm_client: LLMClient,
        schema_introspector: SchemaIntrospector,
        max_rows: int = 100
    ):
        """
        初始化 SQL 查询工具

        Args:
            llm_client: LLM 客户端
            schema_introspector: Schema introspector
            max_rows: 最大返回行数
        """
        self.llm_client = llm_client
        self.schema_introspector = schema_introspector
        self.max_rows = max_rows

        self._definition = ToolDefinition(
            name="sql_query",
            description="将自然语言转换为 SQL 查询并执行，返回查询结果。只支持 SELECT 查询。",
            category="database",
            parameters=[
                {
                    "name": "question",
                    "type": "string",
                    "required": True,
                    "description": "用户用自然语言描述的查询需求"
                },
                {
                    "name": "schema_context",
                    "type": "string",
                    "required": False,
                    "description": "可选的额外 schema 上下文，用于特定表查询"
                }
            ],
            timeout=60
        )

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行自然语言查询

        Args:
            question: 自然语言问题

        Returns:
            {
                "success": bool,
                "sql": str,  # 生成的 SQL
                "results": list,  # 查询结果
                "columns": list,  # 列名
                "row_count": int,  # 结果行数
                "error": str  # 错误信息
            }
        """
        question = kwargs.get("question", "")
        schema_context = kwargs.get("schema_context", "")

        if not question:
            return {
                "success": False,
                "sql": "",
                "results": [],
                "columns": [],
                "row_count": 0,
                "error": "question 参数不能为空"
            }

        try:
            # 1. 获取 schema 信息
            schema_summary = self.schema_introspector.generate_schema_summary()
            if schema_context:
                schema_summary += "\n\n## 额外上下文\n" + schema_context

            # 2. 生成 SQL
            sql = self._generate_sql(question, schema_summary)
            if not sql:
                return {
                    "success": False,
                    "sql": "",
                    "results": [],
                    "columns": [],
                    "row_count": 0,
                    "error": "无法生成有效的 SQL 查询"
                }

            # 3. 验证 SQL 安全性
            is_safe, error_msg = self._validate_sql(sql)
            if not is_safe:
                return {
                    "success": False,
                    "sql": sql,
                    "results": [],
                    "columns": [],
                    "row_count": 0,
                    "error": f"SQL 安全验证失败: {error_msg}"
                }

            # 4. 执行 SQL
            result = self._execute_sql(sql)

            return {
                "success": result.success,
                "sql": sql,
                "results": result.rows[:self.max_rows],
                "columns": result.columns,
                "row_count": min(result.row_count, self.max_rows),
                "execution_time_ms": result.execution_time_ms,
                "error": result.error,
                "truncated": result.row_count > self.max_rows
            }

        except Exception as e:
            return {
                "success": False,
                "sql": "",
                "results": [],
                "columns": [],
                "row_count": 0,
                "error": f"执行出错: {str(e)}"
            }

    def _generate_sql(self, question: str, schema_summary: str) -> Optional[str]:
        """使用 LLM 生成 SQL"""
        prompt = f"""你是一个 SQL 专家，负责将自然语言问题转换为 PostgreSQL SQL 查询。

## 数据库 Schema
{schema_summary}

## 查询需求
{question}

## 要求
1. 只生成 SELECT 查询（不支持 INSERT、UPDATE、DELETE 等操作）
2. 表名和列名必须与上面的 Schema 完全匹配
3. 使用标准的 PostgreSQL 语法
4. 如果需要 LIMIT，默认限制 100 行
5. 只返回 SQL 语句，不要有其他解释

## 输出格式
直接返回 SQL 语句，不要用 markdown 代码块包裹。

SQL:"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )

            # 清理 SQL - 移除可能的 markdown 代码块标记
            sql = response.strip()
            sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
            sql = re.sub(r"^```\s*", "", sql)
            sql = re.sub(r"\s*```$", "", sql)
            sql = sql.strip()

            return sql if sql else None

        except Exception as e:
            print(f"SQL generation error: {e}")
            return None

    def _validate_sql(self, sql: str) -> tuple:
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
            # 精确匹配，避免误报（如 "UPDATE" 在 "UP/DATE" 中不算）
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

    def _execute_sql(self, sql: str) -> SQLResult:
        """执行 SQL 并返回结果"""
        import time
        from psycopg2 import connect as pg_connect

        connection_params = self.schema_introspector.connection_params.copy()
        database = connection_params.pop("database")

        start_time = time.time()

        try:
            conn = pg_connect(database=database, **connection_params)
            with conn.cursor() as cur:
                cur.execute(sql)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()
                row_count = len(rows)

            conn.close()

            execution_time = (time.time() - start_time) * 1000

            return SQLResult(
                success=True,
                rows=rows,
                columns=columns,
                row_count=row_count,
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return SQLResult(
                success=False,
                rows=[],
                columns=[],
                row_count=0,
                execution_time_ms=execution_time,
                error=str(e)
            )

    def format_results(self, results: Dict[str, Any]) -> str:
        """格式化查询结果为可读文本"""
        if not results["success"]:
            return f"查询失败: {results.get('error', '未知错误')}"

        if not results["results"]:
            return "查询成功，但没有返回任何结果。"

        lines = []
        lines.append(f"查询成功，返回 {results['row_count']} 行:\n")

        columns = results["columns"]
        rows = results["results"]

        # 构建表格
        col_widths = [len(c) for c in columns]
        for row in rows:
            for i, val in enumerate(row):
                val_str = str(val) if val is not None else "NULL"
                col_widths[i] = max(col_widths[i], min(len(val_str), 50))

        # 表头
        header = " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(columns))
        separator = "-|-".join("-" * w for w in col_widths)
        lines.append(header)
        lines.append(separator)

        # 数据行
        for row in rows[:20]:  # 最多显示 20 行
            row_str = " | ".join(
                str(v) if v is not None else "NULL"
                for i, v in enumerate(row)
            )
            lines.append(row_str)

        if results.get("truncated"):
            lines.append(f"\n... (结果被截断，仅显示前 {self.max_rows} 行)")

        return "\n".join(lines)
