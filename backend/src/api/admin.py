"""
Admin API routes
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/tools")
async def list_tools():
    """获取所有可用工具"""
    return {
        "tools": [
            {"name": "query_executor", "description": "Execute SQL query"},
            {"name": "slow_query_analyzer", "description": "Analyze slow queries"},
            {"name": "index_analyzer", "description": "Analyze index health"},
            {"name": "backup_manager", "description": "Manage database backups"},
        ]
    }


@router.get("/health")
async def health():
    """系统健康检查"""
    return {"status": "ok", "llm": "connected"}
