"""
Chat API routes
流式输出支持
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import json

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    tool_used: Optional[str] = None
    success: bool = True


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """发送聊天消息（非流式）"""
    # TODO: 调用 LLM 和意图分析
    return ChatResponse(
        message="This is a placeholder response. Connect LLM to enable chat.",
        session_id=request.session_id or "new-session",
        tool_used=None
    )


@router.get("/stream")
async def chat_stream(message: str, session_id: Optional[str] = None):
    """流式聊天"""

    async def generate() -> AsyncGenerator[str, None]:
        # TODO: 实现真实的 LLM 调用和流式输出
        # 目前返回模拟流式数据
        import asyncio

        # 模拟流式输出
        response_text = "你好！我是一个数据库助手。你可以问我关于数据库的问题，比如：\n\n"
        response_text += "1. 查询数据库状态\n"
        response_text += "2. 分析慢查询\n"
        response_text += "3. 查看索引健康\n"
        response_text += "4. 执行 SQL 查询\n\n"
        response_text += "请告诉我你需要什么帮助？"

        for char in response_text:
            yield f"data: {json.dumps({'content': char})}\n\n"
            await asyncio.sleep(0.02)  # 模拟打字效果

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/tool")
async def chat_with_tool(request: ChatRequest):
    """使用工具的聊天"""
    # TODO: 实现完整的意图分析 + 工具调用流程
    return ChatResponse(
        message="Tool calling not yet implemented.",
        session_id=request.session_id or "new-session",
        tool_used=None,
        success=False
    )
