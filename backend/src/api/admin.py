"""
Admin API routes
系统管理接口
"""
from fastapi import APIRouter

router = APIRouter()


def get_all_tools():
    """获取所有工具列表"""
    from src.plugins.registry import get_registry
    from src.plugins.builtin import register_all

    registry = get_registry()
    # 注册所有内置插件
    register_all(registry)

    tools = []
    for plugin in registry.list_all():
        tools.append({
            "name": plugin.name,
            "description": plugin.description,
            "parameters": plugin.parameters
        })
    return tools


@router.get("/tools")
async def list_tools():
    """获取所有可用工具"""
    return {"tools": get_all_tools()}


@router.get("/health")
async def health():
    """系统健康检查"""
    from src.config import get_config
    config = get_config()
    return {
        "status": "ok",
        "llm_configured": bool(config.get("llm", {}).get("api_key"))
    }


@router.get("/")
async def root():
    """API 根路径"""
    return {
        "service": "DBA Assistant API",
        "version": "0.1.0",
        "endpoints": [
            "/api/chat",
            "/api/db",
            "/api/admin/tools"
        ]
    }
