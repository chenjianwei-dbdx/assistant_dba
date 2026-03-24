"""
Chat API routes
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    tool_used: str | None = None


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """发送聊天消息"""
    # TODO: 调用 LLM 和意图分析
    return ChatResponse(
        message="This is a placeholder response",
        session_id=request.session_id or "new-session",
        tool_used=None
    )
