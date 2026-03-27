"""
Database API routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


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
    from src.config import get_config
    return get_config().get("database", {})


@router.get("/connections")
async def list_connections():
    """获取所有连接"""
    from src.db.manager import get_connection_manager
    manager = get_connection_manager(get_db_config())
    return {"connections": manager.list_connections()}


@router.post("/connections")
async def create_connection(conn: ConnectionCreate):
    """创建新连接"""
    from src.db.manager import get_connection_manager
    manager = get_connection_manager(get_db_config())
    result = manager.create_connection(conn.model_dump())
    return result.to_dict()


@router.delete("/connections/{connection_id}")
async def delete_connection(connection_id: str):
    """删除连接"""
    from src.db.manager import get_connection_manager
    manager = get_connection_manager(get_db_config())
    success = manager.delete_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"success": True}


@router.post("/connections/test")
async def test_connection(conn: ConnectionTest):
    """测试连接"""
    from src.db.manager import get_connection_manager
    manager = get_connection_manager(get_db_config())
    return manager.test_connection(conn.model_dump())


@router.post("/query")
async def execute_query(req: QueryRequest):
    """执行 SQL 查询"""
    from src.db.manager import get_connection_manager
    from sqlalchemy import text
    import time

    manager = get_connection_manager(get_db_config())
    conn = manager.get_connection(req.connection_id)

    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        # 获取连接字符串并执行查询
        engine = conn.get_connection_string()
        from sqlalchemy import create_engine

        with create_engine(engine).connect() as db_conn:
            start = time.time()
            result = db_conn.execute(text(req.sql))
            rows = result.fetchmany(req.limit)
            columns = result.keys()
            execution_time = int((time.time() - start) * 1000)

            return {
                "columns": list(columns),
                "rows": [dict(zip(columns, row)) for row in rows],
                "row_count": len(rows),
                "execution_time_ms": execution_time
            }
    except Exception as e:
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time_ms": 0,
            "error": str(e)
        }
