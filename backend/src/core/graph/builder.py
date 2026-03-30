"""LangGraph StateGraph Builder for DBA Assistant"""
from langgraph.graph import StateGraph, END

from .state import ConversationState
from .nodes import intent_node, tool_node, qa_node, clarification_node
from .edges import (
    route_after_intent,
    route_after_tool,
    route_after_qa,
    route_after_clarification
)


def build_conversation_graph() -> StateGraph:
    """构建对话 StateGraph

    节点:
        intent_node → 分析意图
        tool_node → 执行工具
        qa_node → 问答回复
        clarification_node → 参数澄清

    边:
        intent_node → (tool_node | clarification_node | qa_node) [条件边]
        tool_node → END
        qa_node → END
        clarification_node → intent_node
    """
    # 定义状态 schema
    builder = StateGraph(ConversationState)

    # 添加节点
    builder.add_node("intent_node", intent_node)
    builder.add_node("tool_node", tool_node)
    builder.add_node("qa_node", qa_node)
    builder.add_node("clarification_node", clarification_node)

    # 设置入口点
    builder.set_entry_point("intent_node")

    # 添加 intent_node 的条件边
    builder.add_conditional_edges(
        "intent_node",
        route_after_intent,
        {
            "tool_node": "tool_node",
            "qa_node": "qa_node",
            "clarification_node": "clarification_node"
        }
    )

    # tool_node 和 qa_node 结束
    builder.add_edge("tool_node", END)
    builder.add_edge("qa_node", END)

    # clarification_node 回到 intent_node
    builder.add_conditional_edges(
        "clarification_node",
        route_after_clarification,
        {"intent_node": "intent_node"}
    )

    return builder.compile()


# 全局单例
_graph_instance = None


def get_graph() -> StateGraph:
    """获取已编译的对话图（单例）"""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_conversation_graph()
    return _graph_instance


def reset_graph():
    """重置图实例（用于测试或配置变更后）"""
    global _graph_instance
    _graph_instance = None