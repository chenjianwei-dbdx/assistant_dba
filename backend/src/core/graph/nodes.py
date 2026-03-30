"""LangGraph Node Implementations for DBA Assistant"""
from typing import Literal
import json
import re

from .state import ConversationState, Message
from .prompts import intent_prompt, qa_prompt, format_tools_for_prompt


def intent_node(state: ConversationState, config: dict) -> dict:
    """分析用户意图节点

    Args:
        state: ConversationState，包含 messages[-1] 的用户消息
        config: {"configurable": {"llm_client": LLMClient, "tools": [...]}}

    Returns:
        更新 state 的 dict，会被合并
    """
    llm_client = config["configurable"]["llm_client"]
    tools = config["configurable"].get("tools", [])

    # 获取用户最新消息
    user_message = state["messages"][-1]["content"]

    # 格式化工具描述
    tools_desc = format_tools_for_prompt(tools)

    # 调用 LLM
    prompt = intent_prompt.invoke({
        "tools_description": tools_desc,
        "user_input": user_message
    })
    response = llm_client.chat(prompt.to_messages(), temperature=0.0)

    # 解析 JSON 响应
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(0))
        except json.JSONDecodeError:
            result = {"intent": "unknown", "tool_name": None, "confidence": 0.0}
    else:
        result = {"intent": "unknown", "tool_name": None, "confidence": 0.0}

    # 更新状态
    return {
        "intent_result": result,
        "current_tool": result.get("tool_name"),
        "extracted_params": result.get("extracted_params", {}),
        "missing_params": result.get("missing_params", [])
    }


def tool_node(state: ConversationState, config: dict) -> dict:
    """工具执行节点

    Args:
        state: ConversationState（包含 current_tool, extracted_params）
        config: {"configurable": {"registry": PluginRegistry, "context": PluginContext}}

    Returns:
        {"tool_result": {...}, "messages": [...]}（追加到 messages）
    """
    from ...plugins.registry import get_registry

    tool_name = state.get("current_tool")
    params = state.get("extracted_params", {})

    if not tool_name:
        return {"error": "No tool specified"}

    registry = config["configurable"].get("registry") or get_registry()
    tool = registry.get(tool_name)

    if not tool:
        error_msg = f"Tool '{tool_name}' not found"
        return {
            "error": error_msg,
            "tool_result": {"success": False, "error": error_msg}
        }

    # 执行工具
    context = config["configurable"].get("context")
    try:
        result = tool.execute(context, **params)
    except Exception as e:
        result = {"success": False, "error": str(e)}

    # 构建工具消息
    tool_message = Message(
        role="tool",
        content=str(result.get("output", result.get("error", ""))),
        tool_name=tool_name,
        tool_result=result,
        timestamp=None
    )

    return {"tool_result": result, "messages": [tool_message]}


def qa_node(state: ConversationState, config: dict) -> dict:
    """问答节点 - 直接生成回复

    Args:
        state: ConversationState
        config: {"configurable": {"llm_client": LLMClient}}

    Returns:
        {"messages": [AIMessage]}
    """
    llm_client = config["configurable"]["llm_client"]
    user_message = state["messages"][-1]["content"]

    # 获取对话历史（用于上下文）
    chat_history = state["messages"][:-1]
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history]) or "（无历史记录）"

    prompt = qa_prompt.invoke({
        "chat_history": history_str,
        "user_input": user_message
    })

    response = llm_client.chat(prompt.to_messages(), temperature=0.7)

    ai_message = Message(
        role="assistant",
        content=response,
        tool_name=None,
        tool_result=None,
        timestamp=None
    )

    return {"messages": [ai_message]}


def clarification_node(state: ConversationState, config: dict) -> dict:
    """参数澄清节点 - 询问用户补充缺失参数

    Args:
        state: ConversationState（包含 current_tool, missing_params）
        config: {"configurable": {"registry": PluginRegistry}}

    Returns:
        {"messages": [AIMessage]}
    """
    from ...plugins.registry import get_registry

    tool_name = state.get("current_tool")
    missing_params = state.get("missing_params", [])

    registry = config["configurable"].get("registry") or get_registry()
    tool = registry.get(tool_name)

    if not tool:
        lines = [f"请提供以下参数: {', '.join(missing_params)}"]
    else:
        schema = tool.get_schema()
        lines = ["我需要一些参数来完成这个操作："]
        for param_name in missing_params:
            for p in schema.get("parameters", []):
                if p["name"] == param_name:
                    lines.append(f"- **{param_name}**: {p.get('description', '')}")
                    break

    clarification = "\n".join(lines)

    ai_message = Message(
        role="assistant",
        content=clarification,
        tool_name=None,
        tool_result=None,
        timestamp=None
    )

    return {"messages": [ai_message]}