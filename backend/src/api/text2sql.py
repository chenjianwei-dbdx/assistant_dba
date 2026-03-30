"""
Text2SQL API
自然语言转 SQL 的 API 端点（薄路由层）
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from .nl2sql.generate import generate_sql
from .nl2sql.explain import execute_sql, explain_sql

router = APIRouter()


class Text2SQLRequest(BaseModel):
    connection_id: str
    query: str


class Text2SQLExecuteRequest(BaseModel):
    connection_id: str
    sql: str


class Text2SQLResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


@router.post("/text2sql")
async def text2sql_route(req: Text2SQLRequest) -> Text2SQLResponse:
    """Text2SQL：生成 SQL

    委托给 text2sql.generate 模块处理
    """
    success, data, error = generate_sql(req.connection_id, req.query)

    return Text2SQLResponse(
        success=success,
        data=data,
        error=error
    )


@router.post("/text2sql/execute")
async def execute_route(req: Text2SQLExecuteRequest) -> Text2SQLResponse:
    """Text2SQL：执行 SQL

    委托给 text2sql.explain 模块处理
    """
    success, data, error = execute_sql(req.sql)

    return Text2SQLResponse(
        success=success,
        data=data,
        error=error
    )
