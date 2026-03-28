"""
Database Connection Utility
提供共享的数据库连接
"""
import psycopg2
from src.config import get_config


def get_monitor_connection():
    """获取监控数据库连接（用于性能监控和 AI 分析）"""
    config = get_config()
    monitor_config = config.get("monitor", {})
    db_config = config.get("database", {})

    host = monitor_config.get("host", db_config.get("host", "127.0.0.1"))
    port = monitor_config.get("port", db_config.get("port", 5432))
    user = monitor_config.get("username", db_config.get("username", "cjwdsg"))
    password = monitor_config.get("password", db_config.get("password", ""))
    database = monitor_config.get("database", db_config.get("database", "erp_simulation"))

    return psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )


def execute_query(sql: str, params: tuple = None, fetch: bool = True, fetchmany: int = None):
    """
    执行 SQL 查询

    Args:
        sql: SQL 语句
        params: 参数元组
        fetch: 是否获取结果
        fetchmany: fetchmany 的大小

    Returns:
        (columns, rows) 或 row_count
    """
    conn = get_monitor_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()

        if not fetch:
            return cur.rowcount if cur.rowcount >= 0 else 0

        columns = [desc[0] for desc in cur.description] if cur.description else []

        if fetchmany:
            rows = cur.fetchmany(fetchmany)
        else:
            rows = cur.fetchall()

        cur.close()
        return columns, rows
    finally:
        conn.close()
