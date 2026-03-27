"""
Chat API routes
流式输出支持
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
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


def get_chat_service():
    """获取聊天服务（延迟导入避免循环依赖）"""
    from src.core.llm import LLMClient
    from src.core.service import ChatService
    from src.config import get_config

    config = get_config()
    llm_client = LLMClient(config["llm"])
    return ChatService(llm_client)


@router.post("/")
async def chat(request: ChatRequest):
    """发送聊天消息（非流式）"""
    try:
        service = get_chat_service()
        result = service.process_message(request.message)

        if result["type"] == "tool_result":
            return ChatResponse(
                message=str(result.get("output", result.get("error", ""))),
                session_id=request.session_id or "new-session",
                tool_used=result.get("tool_name"),
                success=result.get("success", True)
            )
        elif result["type"] == "param_clarification":
            return ChatResponse(
                message=result["message"],
                session_id=request.session_id or "new-session",
                tool_used=result.get("tool_name"),
                success=True
            )
        else:
            return ChatResponse(
                message=result.get("message", "OK"),
                session_id=request.session_id or "new-session"
            )
    except Exception as e:
        return ChatResponse(
            message=f"Error: {str(e)}",
            session_id=request.session_id or "new-session",
            success=False
        )


@router.get("/stream")
async def chat_stream(message: str, session_id: Optional[str] = None):
    """流式聊天"""

    async def generate():
        try:
            service = get_chat_service()
            for chunk in service.chat_stream(message):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            error = json.dumps({"type": "error", "error": str(e)}, ensure_ascii=False)
            yield f"data: {error}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

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
    return await chat(request)
