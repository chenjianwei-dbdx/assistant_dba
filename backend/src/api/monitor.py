"""
Performance Monitor API
数据库性能监控端点
"""
from fastapi import APIRouter
import psycopg2

from src.config import get_config

router = APIRouter()


def get_monitor_config() -> dict:
    """获取监控数据库配置"""
    config = get_config()
    monitor_config = config.get("monitor", {})
    # fallback to database config if monitor section not set
    db_config = config.get("database", {})
    return {
        "host": monitor_config.get("host", db_config.get("host", "127.0.0.1")),
        "port": monitor_config.get("port", db_config.get("port", 5432)),
        "user": monitor_config.get("username", db_config.get("username", "cjwdsg")),
        "password": monitor_config.get("password", db_config.get("password", "")),
        "database": monitor_config.get("database", db_config.get("database", "erp_simulation")),
    }


def get_db_connection():
    """获取数据库连接"""
    cfg = get_monitor_config()
    return psycopg2.connect(
        host=cfg["host"],
        port=cfg["port"],
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"]
    )


def get_db_name() -> str:
    """获取当前监控的数据库名"""
    return get_monitor_config()["database"]


@router.get("/overview")
async def get_overview():
    """获取监控概览"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        db_name = get_db_name()
        # 数据库统计
        cur.execute("""
            SELECT numbackends, xact_commit, xact_rollback, blks_hit, blks_read
            FROM pg_stat_database
            WHERE datname = %s
        """, (db_name,))
        db_stats = cur.fetchone()

        # 连接统计
        cur.execute("""
            SELECT COUNT(*) FROM pg_stat_activity
            WHERE datname = %s
        """, (db_name,))
        conn_count = cur.fetchone()[0]

        # 活跃查询数
        cur.execute("""
            SELECT COUNT(*) FROM pg_stat_activity
            WHERE state = 'active' AND datname = %s
        """, (db_name,))
        active_queries = cur.fetchone()[0]

        cur.close()
        conn.close()

        return {
            "success": True,
            "data": {
                "connections": conn_count or 0,
                "active_queries": active_queries or 0,
                "transactions_commit": db_stats[1] if db_stats else 0,
                "transactions_rollback": db_stats[2] if db_stats else 0,
                "block_hits": db_stats[3] if db_stats else 0,
                "block_reads": db_stats[4] if db_stats else 0,
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/slow-queries")
async def get_slow_queries():
    """获取慢查询（基于 pg_stat_statements）"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT query, calls, total_exec_time, mean_exec_time, max_exec_time, min_exec_time
            FROM pg_stat_statements
            WHERE mean_exec_time > 100
            ORDER BY mean_exec_time DESC
            LIMIT 20
        """)

        queries = []
        for row in cur.fetchall():
            queries.append({
                "sql": row[0],
                "calls": row[1],
                "total_time_ms": round(row[2], 2),
                "mean_time_ms": round(row[3], 2),
                "max_time_ms": round(row[4], 2),
                "min_time_ms": round(row[5], 2)
            })

        cur.close()
        conn.close()

        return {"success": True, "data": {"queries": queries}}
    except psycopg2.errors.UndefinedTable:
        return {"success": False, "error": "pg_stat_statements 扩展未启用，请联系 DBA 执行: CREATE EXTENSION pg_stat_statements"}


@router.get("/table-stats")
async def get_table_stats():
    """获取表统计信息"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                schemaname,
                relname,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                n_tup_ins,
                n_tup_upd,
                n_tup_del,
                n_live_tup,
                n_dead_tup
            FROM pg_stat_user_tables
            ORDER BY seq_scan DESC
            LIMIT 20
        """)

        tables = []
        for row in cur.fetchall():
            tables.append({
                "schema": row[0],
                "table": row[1],
                "seq_scans": row[2],
                "seq_rows_read": row[3],
                "index_scans": row[4],
                "index_rows_fetched": row[5],
                "inserts": row[6],
                "updates": row[7],
                "deletes": row[8],
                "live_rows": row[9],
                "dead_rows": row[10]
            })

        cur.close()
        conn.close()

        return {"success": True, "data": {"tables": tables}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/index-stats")
async def get_index_stats():
    """获取索引统计信息"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC
            LIMIT 20
        """)

        indexes = []
        for row in cur.fetchall():
            indexes.append({
                "schema": row[0],
                "table": row[1],
                "index": row[2],
                "scans": row[3],
                "rows_read": row[4],
                "rows_fetched": row[5]
            })

        cur.close()
        conn.close()

        return {"success": True, "data": {"indexes": indexes}}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/connections")
async def get_connection_stats():
    """获取连接统计"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        db_name = get_db_name()
        cur.execute("""
            SELECT state, COUNT(*)
            FROM pg_stat_activity
            WHERE datname = %s
            GROUP BY state
        """, (db_name,))

        states = {}
        total = 0
        for row in cur.fetchall():
            state = row[0] or 'unknown'
            states[state] = row[1]
            total += row[1]

        cur.close()
        conn.close()

        return {
            "success": True,
            "data": {
                "total": total,
                "by_state": states
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/analyze")
async def analyze_performance():
    """AI 分析数据库性能，生成优化建议"""
    from src.core.performance_analyzer import PerformanceAnalyzer
    from src.core.llm import LLMClient
    from src.config import get_config

    try:
        config = get_config()
        llm_client = LLMClient(config.get("llm", {}))
        analyzer = PerformanceAnalyzer(llm_client)

        # 收集数据
        conn = get_db_connection()
        cur = conn.cursor()
        db_name = get_db_name()

        # 获取概览数据
        cur.execute("""
            SELECT numbackends, xact_commit, xact_rollback, blks_hit, blks_read
            FROM pg_stat_database WHERE datname = %s
        """, (db_name,))
        db_stats = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE datname = %s", (db_name,))
        conn_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active' AND datname = %s", (db_name,))
        active_queries = cur.fetchone()[0]

        block_hits = db_stats[3] if db_stats else 0
        block_reads = db_stats[4] if db_stats else 0
        hit_rate = "100"
        if block_reads > 0:
            hit_rate = f"{(block_hits / (block_hits + block_reads) * 100):.1f}"

        overview = {
            "connections": conn_count,
            "active_queries": active_queries,
            "hit_rate": hit_rate,
            "commit": db_stats[1] if db_stats else 0,
            "rollback": db_stats[2] if db_stats else 0,
        }

        # 获取表统计
        cur.execute("""
            SELECT schemaname, relname, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch,
                   n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
            FROM pg_stat_user_tables ORDER BY seq_scan DESC LIMIT 20
        """)
        table_stats = []
        for row in cur.fetchall():
            table_stats.append({
                "schema": row[0],
                "table": row[1],
                "seq_scans": row[2],
                "seq_rows_read": row[3],
                "index_scans": row[4],
                "index_rows_fetched": row[5],
                "inserts": row[6],
                "updates": row[7],
                "deletes": row[8],
                "live_rows": row[9],
                "dead_rows": row[10]
            })

        cur.close()
        conn.close()

        # AI 分析
        result = analyzer.analyze(overview, table_stats)

        return result

    except Exception as e:
        return {"success": False, "error": str(e), "suggestions": [], "analysis": ""}
