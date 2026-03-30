"""Prompt templates for LangGraph nodes"""
from langchain_core.prompts import ChatPromptTemplate


# ============ Intent Node ============
INTENT_SYSTEM_PROMPT = """你是一个数据库助手，负责分析用户意图。

可用工具：
{tools_description}

输出格式（必须严格遵循 JSON）：
{{"intent": "tool_use|qa|unknown", "tool_name": "...", "confidence": 0.0-1.0, "reasoning": "...", "extracted_params": {{}}, "missing_params": []}}

规则：
- intent="tool_use": 用户想执行某个工具
- intent="qa": 用户想获取信息或聊天
- intent="unknown": 无法确定意图
- tool_name 必须是可用工具之一
- missing_params 列出缺失的必填参数"""

INTENT_HUMAN_PROMPT = "{user_input}"

intent_prompt = ChatPromptTemplate.from_messages([
    ("system", INTENT_SYSTEM_PROMPT),
    ("human", INTENT_HUMAN_PROMPT)
])


# ============ QA Node ============
QA_SYSTEM_PROMPT = """你是一个友好的数据库助手。请用简洁清晰的语言回答用户的问题。

对话历史：
{chat_history}"""

QA_HUMAN_PROMPT = "{user_input}"

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", QA_SYSTEM_PROMPT),
    ("human", QA_HUMAN_PROMPT)
])


# ============ Clarification Node ============
CLARIFICATION_PROMPT = """需要补充以下参数才能执行工具 {tool_name}：

{missing_params_list}

请用自然语言询问用户补充这些参数。"""



def format_tools_for_prompt(tools: list) -> str:
    """将工具列表格式化为 prompt 字符串

    Args:
        tools: 工具定义列表，每个元素包含 name, description, parameters

    Returns:
        格式化的工具描述字符串
    """
    lines = []
    for tool in tools:
        params = ", ".join([p["name"] for p in tool.get("parameters", [])]) or "无"
        lines.append(f"- {tool['name']}({params}): {tool['description']}")
    return "\n".join(lines)