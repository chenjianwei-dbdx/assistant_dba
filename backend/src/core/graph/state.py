"""LangGraph State Definition for DBA Assistant"""
from typing import TypedDict, Annotated, Sequence, Optional
from datetime import datetime
from langgraph.graph import add_messages


class Message(TypedDict):
    """Single message in conversation"""
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    tool_name: Optional[str]
    tool_result: Optional[dict]
    timestamp: Optional[datetime]


class ConversationState(TypedDict):
    """Main LangGraph state for conversation"""
    messages: Annotated[Sequence[Message], add_messages]
    session_id: Optional[str]
    current_tool: Optional[str]
    extracted_params: dict
    missing_params: list[str]
    intent_result: Optional[dict]
    tool_result: Optional[dict]
    error: Optional[str]