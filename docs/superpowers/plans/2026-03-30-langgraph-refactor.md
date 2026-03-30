# LangGraph 重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有自定义 Agent 架构迁移到 LangGraph，实现真正的 ReAct 循环 + 状态管理

**Architecture:** 核心是 `StateGraph`，包含 intent_node、tool_node、response_node 三个主节点。工具执行建模为子图。NL2SQL pipeline 作为独立的 tool_node 内部 DAG。对话历史通过 state 显式管理。

**Tech Stack:** LangGraph、LangChain (langchain-core, langchain-community)、FastAPI、SQLAlchemy、psycopg2

---

## 现状分析

| 组件 | 当前实现 | LangGraph 对应 |
|------|---------|--------------|
| 对话状态 | **无**（完全无状态） | `state["messages"]` |
| 意图分析 | 单 prompt → JSON | `intent_node` |
| 工具选择 | IntentAnalyzer 内置 | `tool_node` (via Tool Calling) |
| 工具执行 | PluginRegistry + DBATool | `PluginContext` via `tool_node` |
| NL2SQL | 3-Layer 串行 | 子图 `nl2sql_graph` |
| Prompt | 硬编码 f-string | `PromptTemplate` 外部化 |

---

## 文件结构

```
backend/src/
├── main.py                           # FastAPI 入口（修改：初始化 LangGraph）
├── config.py                         # 配置（修改：新增 langchain 相关配置）
├── core/
│   ├── llm.py                        # 保留，LangChain 作为底层
│   ├── graph/                        # 【新建】LangGraph 核心
│   │   ├── __init__.py
│   │   ├── state.py                  # 状态定义 + StateSchema
│   │   ├── nodes.py                  # 所有节点实现
│   │   ├── edges.py                 # 边定义 + 条件边
│   │   ├── builder.py                # StateGraph 构造器
│   │   └── prompts.py                # Prompt 模板（从硬编码迁移）
│   ├── intent.py                     # 【废弃】逻辑迁移到 nodes.py
│   ├── service.py                    # 【废弃】逻辑迁移到 graph
│   ├── dependencies.py               # 【修改】统一 DI 容器
│   └── errors.py                     # 保留
├── plugins/
│   ├── base.py                       # 保留（DBATool 基类）
│   ├── registry.py                   # 【修改】实现 langchain.tools
│   └── builtin/
│       └── __init__.py              # 【修改】使用 langchain.toolkits
├── agents/                          # NL2SQL（保留，子图化）
│   ├── table_selector.py
│   ├── sql_generator.py
│   └── result_summarizer.py
├── db/
│   ├── schema_loader.py              # 保留
│   └── ...
└── api/
    ├── chat.py                       # 【修改】调用 LangGraph
    └── nl2sql/
        ├── generate.py              # 【修改】作为子图
        └── explain.py
```

---

## Task 1: 初始化 LangChain 依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加 LangChain 依赖**

```txt
# backend/requirements.txt 新增
langchain-core>=0.1.0
langchain-community>=0.0.10
langgraph>=0.0.20
```

- [ ] **Step 2: 安装依赖**

Run: `cd /Users/cjwdsg/smart-assistant/backend && pip install langchain-core langchain-community langgraph`

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "deps: add langchain-core, langgraph dependencies"
```

---

## Task 2: 定义 LangGraph State Schema

**Files:**
- Create: `backend/src/core/graph/state.py`
- Create: `backend/src/core/graph/__init__.py`

- [ ] **Step 1: 编写 State 测试**

```python
# tests/core/graph/test_state.py
import pytest
from datetime import datetime

def test_conversation_state_initialization():
    from core.graph.state import ConversationState

    state = ConversationState()
    assert state["messages"] == []
    assert state["session_id"] is None
    assert state["current_tool"] is None
    assert state["extracted_params"] == {}

def test_conversation_state_with_messages():
    from core.graph.state import ConversationState

    state = ConversationState(
        messages=[{"role": "user", "content": "hello"}],
        session_id="test-123"
    )
    assert len(state["messages"]) == 1
    assert state["session_id"] == "test-123"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /Users/cjwdsg/smart-assistant/backend && pytest tests/core/graph/test_state.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 创建 state.py**

```python
# backend/src/core/graph/state.py
"""LangGraph State Definition for DBA Assistant"""
from typing import TypedDict, Annotated, Sequence
from datetime import datetime
from langgraph.graph import add_messages


class Message(TypedDict):
    """Single message in conversation"""
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    tool_name: str | None
    tool_result: dict | None
    timestamp: datetime


class ExtractedParams(TypedDict):
    """Extracted parameters for tool execution"""
    tool_name: str | None
    params: dict


class ConversationState(TypedDict):
    """Main LangGraph state for conversation"""
    messages: Annotated[Sequence[Message], add_messages]
    session_id: str | None
    current_tool: str | None
    extracted_params: dict
    missing_params: list[str]
    intent_result: dict | None
    tool_result: dict | None
    error: str | None
```

- [ ] **Step 4: 创建 __init__.py**

```python
# backend/src/core/graph/__init__.py
from .state import ConversationState, Message, ExtractedParams

__all__ = ["ConversationState", "Message", "ExtractedParams"]
```

- [ ] **Step 5: 运行测试验证通过**

Run: `cd /Users/cjwdsg/smart-assistant/backend && pytest tests/core/graph/test_state.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/core/graph/ tests/core/graph/test_state.py
git commit -m "feat: add LangGraph state schema"
```

---

## Task 3: 创建 Prompt 模板（Prompt 外部化）

**Files:**
- Create: `backend/src/core/graph/prompts.py`
- Modify: `backend/configs/prompts.yaml`（已有，扩展）

- [ ] **Step 1: 迁移 intent_prompt 到 prompts.py**

```python
# backend/src/core/graph/prompts.py
"""Prompt templates for LangGraph nodes"""
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# ============ Intent Node ============
INTENT_SYSTEM_PROMPT = """你是一个数据库助手，负责分析用户意图。

可用工具：
{tools_description}

输出格式（必须严格遵循）：
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

# ============ Tool Execution Node ============
TOOL_SYSTEM_PROMPT = """你是一个工具执行助手。根据用户请求和已提取的参数，执行相应的工具。

上下文：
- 当前工具: {tool_name}
- 已提取参数: {extracted_params}
- 用户原始请求: {user_input}"""

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
    """将工具列表格式化为 prompt 字符串"""
    lines = []
    for tool in tools:
        params = ", ".join([p["name"] for p in tool.get("parameters", [])]) or "无"
        lines.append(f"- {tool['name']}({params}): {tool['description']}")
    return "\n".join(lines)
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/core/graph/prompts.py
git commit -m "feat: externalize prompts to langgraph prompts module"
```

---

## Task 4: 实现 LangGraph 节点（Nodes）

**Files:**
- Create: `backend/src/core/graph/nodes.py`

- [ ] **Step 1: 编写节点测试**

```python
# tests/core/graph/test_nodes.py
import pytest
from unittest.mock import MagicMock, patch

def test_intent_node_routes_to_tool():
    from core.graph.nodes import intent_node

    mock_state = {"messages": [{"role": "user", "content": "查询最近的慢查询"}]}
    mock_config = {"configurable": {"llm_client": MagicMock(), "tools": []}}

    # Mock LLM response
    with patch("core.graph.nodes.get_llm_client") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = '{"intent": "tool_use", "tool_name": "slow_query_analyzer", "confidence": 0.9}'
        mock_get_llm.return_value = mock_llm

        result = intent_node(mock_state, mock_config)
        assert result["intent_result"]["intent"] == "tool_use"
        assert result["current_tool"] == "slow_query_analyzer"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /Users/cjwdsg/smart-assistant/backend && pytest tests/core/graph/test_nodes.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 实现 intent_node**

```python
# backend/src/core/graph/nodes.py
"""LangGraph Node Implementations"""
from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from .state import ConversationState
from .prompts import intent_prompt, qa_prompt, format_tools_for_prompt


def intent_node(state: ConversationState, config: dict) -> dict:
    """分析用户意图节点

    Args:
        state: ConversationState
        config: {"configurable": {"llm_client": LLMClient, "tools": [...]}}

    Returns:
        更新 state 的 dict（会被合并）
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
    import json, re
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        result = json.loads(match.group(0))
    else:
        result = {"intent": "unknown", "tool_name": None, "confidence": 0.0}

    # 更新状态
    updates = {
        "intent_result": result,
        "current_tool": result.get("tool_name"),
        "extracted_params": result.get("extracted_params", {}),
        "missing_params": result.get("missing_params", [])
    }

    return updates


def tool_node(state: ConversationState, config: dict) -> dict:
    """工具执行节点

    Args:
        state: ConversationState（包含 current_tool, extracted_params）
        config: {"configurable": {"registry": PluginRegistry, "context": PluginContext}}

    Returns:
        {"tool_result": {...}, "messages": [...]}（追加到 messages）
    """
    from ..plugins.registry import get_registry

    tool_name = state.get("current_tool")
    params = state.get("extracted_params", {})

    if not tool_name:
        return {"error": "No tool specified"}

    registry = config["configurable"].get("registry") or get_registry()
    tool = registry.get(tool_name)

    if not tool:
        return {"error": f"Tool '{tool_name}' not found"}

    # 执行工具
    context = config["configurable"].get("context")
    try:
        result = tool.execute(context, **params)
    except Exception as e:
        result = {"success": False, "error": str(e)}

    # 构建工具消息
    tool_message = {
        "role": "tool",
        "content": str(result.get("output", result.get("error", ""))),
        "tool_name": tool_name,
        "tool_result": result
    }

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

    prompt = qa_prompt.invoke({
        "chat_history": "\n".join([f"{m['role']}: {m['content']}" for m in chat_history]),
        "user_input": user_message
    })

    response = llm_client.chat(prompt.to_messages(), temperature=0.7)

    ai_message = {
        "role": "assistant",
        "content": response,
        "tool_name": None,
        "tool_result": None
    }

    return {"messages": [ai_message]}


def clarification_node(state: ConversationState, config: dict) -> dict:
    """参数澄清节点 - 询问用户补充缺失参数

    Args:
        state: ConversationState（包含 current_tool, missing_params）
        config: {"configurable": {"registry": PluginRegistry}}

    Returns:
        {"messages": [AIMessage]}
    """
    from ..plugins.registry import get_registry

    tool_name = state.get("current_tool")
    missing_params = state.get("missing_params", [])

    registry = config["configurable"].get("registry") or get_registry()
    tool = registry.get(tool_name)

    if not tool:
        clarification = f"请提供以下参数: {', '.join(missing_params)}"
    else:
        schema = tool.get_schema()
        lines = ["我需要一些参数来完成这个操作："]
        for param_name in missing_params:
            for p in schema.get("parameters", []):
                if p["name"] == param_name:
                    lines.append(f"- **{param_name}**: {p.get('description', '')}")
                    break
        clarification = "\n".join(lines)

    ai_message = {
        "role": "assistant",
        "content": clarification,
        "tool_name": None,
        "tool_result": None
    }

    return {"messages": [ai_message]}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd /Users/cjwdsg/smart-assistant/backend && pytest tests/core/graph/test_nodes.py -v`
Expected: PASS (or partially passing with mocks)

- [ ] **Step 5: Commit**

```bash
git add backend/src/core/graph/nodes.py tests/core/graph/test_nodes.py
git commit -m "feat: implement langgraph nodes (intent, tool, qa, clarification)"
```

---

## Task 5: 定义边（Edges）和条件路由

**Files:**
- Create: `backend/src/core/graph/edges.py`

- [ ] **Step 1: 实现边路由逻辑**

```python
# backend/src/core/graph/edges.py
"""LangGraph Edge Definitions and Conditional Routing"""
from typing import Literal

from .state import ConversationState


def route_after_intent(state: ConversationState) -> Literal["tool_node", "qa_node", "clarification_node"]:
    """intent_node 之后的路由

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

    - 工具执行成功 → 继续意图分析（看是否需要更多工具）
    - 或者直接结束

    目前简化：工具执行完就结束
    """
    tool_result = state.get("tool_result", {})
    if tool_result.get("success"):
        return "__end__"
    return "__end__"


def route_after_qa(state: ConversationState) -> Literal["intent_node", "__end__"]:
    """qa_node 之后的路由"""
    return "__end__"


def route_after_clarification(state: ConversationState) -> Literal["tool_node"]:
    """clarification_node 之后的路由

    假设用户补充参数后会再次调用 intent_node，
    实际上这里直接回到 intent_node
    """
    return "intent_node"
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/core/graph/edges.py
git commit -m "feat: add langgraph edge routing logic"
```

---

## Task 6: 构建 StateGraph

**Files:**
- Create: `backend/src/core/graph/builder.py`

- [ ] **Step 1: 实现图构造器**

```python
# backend/src/core/graph/builder.py
"""LangGraph StateGraph Builder"""
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

    # 添加边
    builder.add_conditional_edges(
        "intent_node",
        route_after_intent,
        {
            "tool_node": "tool_node",
            "qa_node": "qa_node",
            "clarification_node": "clarification_node"
        }
    )

    builder.add_edge("tool_node", END)
    builder.add_edge("qa_node", END)
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
```

- [ ] **Step 2: 编写集成测试**

```python
# tests/core/graph/test_builder.py
import pytest
from unittest.mock import MagicMock


def test_graph_routes_qa_to_end():
    from core.graph.builder import build_conversation_graph

    graph = build_conversation_graph()
    assert graph is not None

    # 验证图结构
    nodes = graph.nodes.keys()
    assert "intent_node" in nodes
    assert "tool_node" in nodes
    assert "qa_node" in nodes
    assert "clarification_node" in nodes


def test_graph_invoke_qa():
    from core.graph.builder import build_conversation_graph

    graph = build_conversation_graph()

    initial_state = {
        "messages": [{"role": "user", "content": "你好"}],
        "session_id": "test-123",
        "current_tool": None,
        "extracted_params": {},
        "missing_params": [],
        "intent_result": {"intent": "qa", "confidence": 0.9},
        "tool_result": None,
        "error": None
    }

    config = {
        "configurable": {
            "llm_client": MagicMock(),
            "tools": [],
            "registry": MagicMock()
        }
    }

    # Mock LLM
    config["configurable"]["llm_client"].chat.return_value = "你好！有什么可以帮助你的吗？"

    result = graph.invoke(initial_state, config=config)
    assert "messages" in result
    assert len(result["messages"]) >= 2  # user + assistant
```

- [ ] **Step 3: 运行测试**

Run: `cd /Users/cjwdsg/smart-assistant/backend && pytest tests/core/graph/test_builder.py -v`

- [ ] **Step 4: Commit**

```bash
git add backend/src/core/graph/builder.py tests/core/graph/test_builder.py
git commit -m "feat: implement langgraph stategraph builder"
```

---

## Task 7: 集成到 FastAPI（修改 API 路由）

**Files:**
- Modify: `backend/src/api/chat.py`

- [ ] **Step 1: 编写新 chat API 测试**

```python
# tests/api/test_chat_langgraph.py
import pytest


def test_chat_endpoint_with_langgraph():
    # TODO: 实现 FastAPI 测试
    pass
```

- [ ] **Step 2: 修改 chat.py 使用 LangGraph**

```python
# backend/src/api/chat.py
"""Chat API - 使用 LangGraph"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..core.graph.builder import get_graph
from ..core.graph.state import ConversationState
from ..core.dependencies import get_llm_client, get_registry, get_plugin_context
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


@router.post("/")
async def chat(req: ChatRequest) -> ChatResponse:
    """处理对话请求（通过 LangGraph）"""
    graph = get_graph()

    # 获取依赖
    llm_client = get_llm_client()
    registry = get_registry()
    context = get_plugin_context()

    # 构建初始状态
    initial_state: ConversationState = {
        "messages": [{"role": "user", "content": req.message}],
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
            "tools": registry.get_tools_for_prompt(),
            "registry": registry,
            "context": context
        }
    }

    # 执行图
    try:
        result = graph.invoke(initial_state, config=config)
    except Exception as e:
        raise DBAError(f"Graph execution failed: {e}")

    # 提取最后一条 assistant 消息
    assistant_messages = [m for m in result.get("messages", []) if m["role"] == "assistant"]
    if assistant_messages:
        response_text = assistant_messages[-1]["content"]
    else:
        response_text = "抱歉，我无法处理这个请求。"

    return ChatResponse(
        response=response_text,
        session_id=result.get("session_id") or req.session_id or "unknown",
        tool_name=result.get("current_tool"),
        success=result.get("tool_result", {}).get("success", True) if result.get("tool_result") else True
    )


@router.get("/stream")
async def chat_stream(message: str, session_id: Optional[str] = None):
    """流式对话（TODO: 实现流式版本）"""
    raise HTTPException(status_code=501, detail="Streaming not yet implemented")
```

- [ ] **Step 3: 运行测试**

Run: `cd /Users/cjwdsg/smart-assistant/backend && pytest tests/api/test_chat_langgraph.py -v`

- [ ] **Step 4: Commit**

```bash
git add backend/src/api/chat.py
git commit -m "feat: integrate langgraph into chat API"
```

---

## Task 8: 统一依赖注入（消除双例）

**Files:**
- Modify: `backend/src/core/dependencies.py`

- [ ] **Step 1: 修改 Container 统一初始化**

```python
# backend/src/core/dependencies.py
"""Dependency Injection Container - 统一管理所有依赖"""
from functools import lru_cache
from .graph.builder import get_graph, reset_graph
from .plugins.registry import PluginRegistry, get_registry


class Container:
    """统一 DI 容器"""

    def __init__(self):
        self._llm_client = None
        self._connection_manager = None
        self._plugin_registry = None
        self._graph = None

    def init(self, config: dict):
        """初始化所有依赖"""
        # LLM Client
        from .llm import LLMClient
        llm_config = config.get("llm", {})
        self._llm_client = LLMClient(llm_config)

        # Plugin Registry
        self._plugin_registry = get_registry()  # 复用全局单例
        from .plugins.builtin import register_all
        register_all(self._plugin_registry)

        # Connection Manager
        from ..db.manager import ConnectionManager
        self._connection_manager = ConnectionManager()

        # LangGraph（延迟初始化）
        # self._graph = get_graph()  # 暂时不自动初始化

    @property
    def llm_client(self):
        return self._llm_client

    @property
    def connection_manager(self):
        return self._connection_manager

    @property
    def plugin_registry(self):
        return self._plugin_registry

    def get_graph(self):
        if self._graph is None:
            from .graph.builder import build_conversation_graph
            self._graph = build_conversation_graph()
        return self._graph

    def reset_graph(self):
        self._graph = None


# 全局容器
_container = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container


# FastAPI 依赖注入函数
@lru_cache()
def get_llm_client():
    return get_container().llm_client


@lru_cache()
def get_connection_manager():
    return get_container().connection_manager


@lru_cache()
def get_plugin_registry():
    return get_container().plugin_registry


@lru_cache()
def get_plugin_context():
    """获取插件执行上下文"""
    from ..plugins.base import PluginContext
    return PluginContext(
        db_manager=get_connection_manager(),
        llm_client=get_llm_client(),
        config={}
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/core/dependencies.py
git commit -m "refactor: unify DI container, support langgraph"
```

---

## Task 9: NL2SQL 作为子图集成（可选，阶段二）

此任务为可选的阶段二目标，暂不执行。

---

## 执行验证

```bash
# 1. 启动后端
cd /Users/cjwdsg/smart-assistant/backend
uvicorn src.main:app --reload --port 8000

# 2. 测试对话 API
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "查询最近的慢查询"}'

# 3. 测试 health
curl http://localhost:8000/health
```

---

## 里程碑总结

| Task | 内容 | 复杂度 |
|------|------|--------|
| Task 1 | LangChain 依赖初始化 | 低 |
| Task 2 | State Schema 定义 | 低 |
| Task 3 | Prompt 模板外部化 | 中 |
| Task 4 | 节点实现 | 高 |
| Task 5 | 边路由定义 | 中 |
| Task 6 | StateGraph 构造 | 高 |
| Task 7 | FastAPI 集成 | 中 |
| Task 8 | 统一 DI 容器 | 低 |

**推荐执行顺序**: Task 1 → 2 → 3 → 8 → 4 → 5 → 6 → 7
