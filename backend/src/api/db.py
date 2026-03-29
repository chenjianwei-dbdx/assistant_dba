"""
Database API routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import time

router = APIRouter()

# 查询历史存储（内存）
_query_history: List[dict] = []
_MAX_HISTORY = 50


class ConnectionCreate(BaseModel):
    name: str
    db_type: str = "mysql"
    host: str = "localhost"
    port: int = 3306
    database: str
    username: str
    password: str
    charset: str = "utf8mb4"


class ConnectionTest(BaseModel):
    name: Optional[str] = None
    db_type: str = "mysql"
    host: str = "localhost"
    port: int = 3306
    database: str
    username: str
    password: str
    charset: str = "utf8mb4"


class QueryRequest(BaseModel):
    connection_id: str
    sql: str
    limit: int = 1000


def get_db_config():
    """获取数据库配置"""
    from src.core.dependencies import get_connection_manager
    return get_connection_manager().config


@router.get("/connections")
async def list_connections():
    """获取所有连接"""
    from src.core.dependencies import get_connection_manager
    manager = get_connection_manager()
    return {"connections": manager.list_connections()}


@router.post("/connections")
async def create_connection(conn: ConnectionCreate):
    """创建新连接"""
    from src.core.dependencies import get_connection_manager
    manager = get_connection_manager()
    result = manager.create_connection(conn.model_dump())
    return result.to_dict()


@router.delete("/connections/{connection_id}")
async def delete_connection(connection_id: str):
    """删除连接"""
    from src.core.dependencies import get_connection_manager
    manager = get_connection_manager()
    success = manager.delete_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"success": True}


@router.post("/connections/test")
async def test_connection(conn: ConnectionTest):
    """测试连接"""
    from src.core.dependencies import get_connection_manager
    manager = get_connection_manager()
    return manager.test_connection(conn.model_dump())


@router.post("/query")
async def execute_query(req: QueryRequest):
    """执行 SQL 查询"""
    from src.db.connection import get_monitor_connection
    from sqlalchemy import text
    import time

    # 优先使用请求中的 connection_id 查找连接
    connection_id = req.connection_id

    try:
        # 使用共享的监控数据库连接
        conn = get_monitor_connection()
        cur = conn.cursor()

        start = time.time()
        cur.execute(req.sql)
        rows = cur.fetchmany(req.limit)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        execution_time = int((time.time() - start) * 1000)

        result_data = {
            "columns": columns,
            "rows": [dict(zip(columns, row)) for row in rows],
            "row_count": len(rows),
            "execution_time_ms": execution_time
        }

        # 添加到历史
        add_to_history(req.sql, connection_id or "monitor", len(rows), execution_time)

        cur.close()
        conn.close()

        return result_data
    except Exception as e:
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time_ms": 0,
            "error": str(e)
        }


@router.post("/query/explain")
async def explain_query(req: QueryRequest):
    """执行 EXPLAIN 查看查询计划"""
    from src.db.connection import get_monitor_connection

    try:
        conn = get_monitor_connection()
        cur = conn.cursor()

        # PostgreSQL 的 EXPLAIN
        explain_sql = f"EXPLAIN (FORMAT TEXT) {req.sql}"
        cur.execute(explain_sql)
        rows = cur.fetchall()

        plan = "\n".join([row[0] for row in rows])

        cur.close()
        conn.close()

        return {
            "success": True,
            "plan": plan
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/query/history")
async def get_query_history():
    """获取查询历史"""
    return {"history": _query_history}


@router.delete("/query/history")
async def clear_query_history():
    """清空查询历史"""
    global _query_history
    _query_history = []
    return {"success": True}


def add_to_history(sql: str, connection_id: str, row_count: int, execution_time_ms: int):
    """添加查询到历史"""
    global _query_history
    entry = {
        "id": len(_query_history) + 1,
        "sql": sql,
        "connection_id": connection_id,
        "row_count": row_count,
        "execution_time_ms": execution_time_ms,
        "created_at": datetime.now().isoformat()
    }
    _query_history.insert(0, entry)
    if len(_query_history) > _MAX_HISTORY:
        _query_history = _query_history[:_MAX_HISTORY]
