"""LangGraph Edge Definitions and Conditional Routing"""
from typing import Literal

from .state import ConversationState


def route_after_intent(state: ConversationState) -> Literal["tool_node", "qa_node", "clarification_node"]:
    """intent_node 之后的路由

    Args:
        state: ConversationState，包含 intent_result

    Returns:
        - "tool_node": intent="tool_use" 且参数齐全
        - "clarification_node": intent="tool_use" 但参数缺失
        - "qa_node": intent="qa" 或 "unknown"
    """
    intent_result = state.get("intent_result", {})
    intent = intent_result.get("intent", "unknown")

    if intent == "tool_use":
        missing_params = intent_result.get("missing_params", [])
        if missing_params:
            return "clarification_node"
        return "tool_node"

    return "qa_node"


def route_after_tool(state: ConversationState) -> Literal["intent_node", "__end__"]:
    """tool_node 之后的路由

    当前简化：工具执行完就结束对话
    未来可扩展：工具执行成功后继续分析是否需要更多工具
    """
    return "__end__"


def route_after_qa(state: ConversationState) -> Literal["intent_node", "__end__"]:
    """qa_node 之后的路由

    当前简化：问答完成就结束对话
    """
    return "__end__"


def route_after_clarification(state: ConversationState) -> Literal["intent_node"]:
    """clarification_node 之后的路由

    用户补充参数后，重新进入 intent_node 分析
    """
    return "intent_node"