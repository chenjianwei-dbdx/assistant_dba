"""
SQL Execution and EXPLAIN Logic
SQL 执行与 EXPLAIN 逻辑
"""
import time
from typing import List, Dict, Any, Optional
from ...db.connection import get_monitor_connection
from ...db.schema_loader import SchemaLoader
from ...db.sql_validator import SQLValidator
from ...agents.result_summarizer import ResultSummarizer
from .generate import get_llm_client


def execute_sql(sql: str) -> tuple[bool, Optional[dict], Optional[str]]:
    """执行 SQL 并返回结果

    Args:
        sql: 要执行的 SQL 语句

    Returns:
        Tuple of (success, data, error)
        - success: 是否成功
        - data: 成功时返回的数据字典，包含 columns, rows, row_count, execution_time_ms, summary
        - error: 失败时返回的错误信息
    """
    schema_loader = SchemaLoader()
    validator = SQLValidator()
    valid_tables = schema_loader.get_all_tables()
    validation = validator.validate(sql, valid_tables)

    if not validation.valid:
        return False, None, validation.error

    # 使用共享数据库连接
    conn = get_monitor_connection()
    cur = conn.cursor()

    start_time = time.time()
    cur.execute(sql)
    rows = cur.fetchmany(1000)
    columns = [desc[0] for desc in cur.description] if cur.description else []
    execution_time_ms = int((time.time() - start_time) * 1000)

    row_dicts = [dict(zip(columns, row)) for row in rows]

    cur.close()
    conn.close()

    # Layer 3: 结果摘要
    llm_client = get_llm_client()
    summarizer = ResultSummarizer(llm_client)
    summary = summarizer.summarize(columns, row_dicts)

    return True, {
        "columns": columns,
        "rows": row_dicts,
        "row_count": len(row_dicts),
        "execution_time_ms": execution_time_ms,
        "summary": summary
    }, None


def explain_sql(sql: str) -> tuple[bool, Optional[dict], Optional[str]]:
    """执行 EXPLAIN 并返回查询计划

    Args:
        sql: 要 EXPLAIN 的 SQL 语句

    Returns:
        Tuple of (success, data, error)
        - success: 是否成功
        - data: 成功时返回的数据字典，包含 plan
        - error: 失败时返回的错误信息
    """
    schema_loader = SchemaLoader()
    validator = SQLValidator()
    valid_tables = schema_loader.get_all_tables()
    validation = validator.validate(sql, valid_tables)

    if not validation.valid:
        return False, None, validation.error

    conn = get_monitor_connection()
    cur = conn.cursor()

    try:
        # 执行 EXPLAIN
        cur.execute(f"EXPLAIN {sql}")
        plan_rows = cur.fetchall()
        plan = "\n".join(row[0] for row in plan_rows)

        cur.close()
        conn.close()

        return True, {"plan": plan}, None

    except Exception as e:
        cur.close()
        conn.close()
        return False, None, f"EXPLAIN 错误: {str(e)}"
