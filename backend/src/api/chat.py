"""Chat API - 使用 LangGraph"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..core.graph.builder import get_graph
from ..core.graph.state import ConversationState, Message
from ..core.dependencies import get_llm_client, get_plugin_registry, get_plugin_context
from ..core.errors import DBAError

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_name: Optional[str] = None
    success: bool


def get_tools_for_graph():
    """获取工具列表，格式化为 LangGraph 可用"""
    try:
        registry = get_plugin_registry()
        tools = registry.list_all()
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters or []
            }
            for t in tools
        ]
    except Exception:
        return []


@router.post("/")
async def chat(req: ChatRequest) -> ChatResponse:
    """处理对话请求（通过 LangGraph）"""
    graph = get_graph()

    # 获取依赖
    llm_client = get_llm_client()
    registry = get_plugin_registry()
    context = get_plugin_context()

    # 构建初始状态
    initial_state: ConversationState = {
        "messages": [
            Message(
                role="user",
                content=req.message,
                tool_name=None,
                tool_result=None,
                timestamp=None
            )
        ],
        "session_id": req.session_id,
        "current_tool": None,
        "extracted_params": {},
        "missing_params": [],
        "intent_result": None,
        "tool_result": None,
        "error": None
    }

    # 配置
    config = {
        "configurable": {
            "llm_client": llm_client,
            "tools": get_tools_for_graph(),
            "registry": registry,
            "context": context
        }
    }

    # 执行图
    try:
        result = graph.invoke(initial_state, config=config)
    except Exception as e:
        raise DBAError(f"Graph execution failed: {str(e)}")

    # 提取最后一条 assistant 消息
    assistant_messages = [m for m in result.get("messages", []) if m.get("role") == "assistant"]
    if assistant_messages:
        response_text = assistant_messages[-1].get("content", "")
    else:
        response_text = "抱歉，我无法处理这个请求。"

    # 提取工具名（如果有）
    tool_name = result.get("current_tool")

    # 判断是否成功
    success = True
    if result.get("tool_result"):
        success = result["tool_result"].get("success", True)

    return ChatResponse(
        response=response_text,
        session_id=result.get("session_id") or req.session_id or "unknown",
        tool_name=tool_name,
        success=success
    )


@router.get("/stream")
async def chat_stream(message: str, session_id: Optional[str] = None):
    """流式对话（TODO: 实现流式版本）"""
    raise HTTPException(status_code=501, detail="Streaming not yet implemented")
