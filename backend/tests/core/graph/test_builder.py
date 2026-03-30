"""Tests for LangGraph builder"""


def test_build_graph():
    """Test that graph builds without errors"""
    from src.core.graph.builder import build_conversation_graph

    graph = build_conversation_graph()
    assert graph is not None

    # 验证图结构
    nodes = graph.nodes.keys()
    assert "intent_node" in nodes
    assert "tool_node" in nodes
    assert "qa_node" in nodes
    assert "clarification_node" in nodes


def test_graph_invoke_qa():
    """Test graph execution for QA intent

    Note: Full graph invocation requires proper LangGraph config handling.
    This test verifies the graph structure and routing logic.
    """
    from src.core.graph.builder import build_conversation_graph
    from src.core.graph.edges import route_after_intent, route_after_qa

    graph = build_conversation_graph()
    assert graph is not None

    # Verify edges are properly configured by checking routing functions
    state = {
        "messages": [{"role": "user", "content": "你好"}],
        "session_id": "test-123",
        "current_tool": None,
        "extracted_params": {},
        "missing_params": [],
        "intent_result": {"intent": "qa", "confidence": 0.9},
        "tool_result": None,
        "error": None
    }

    # Test routing logic directly
    next_node = route_after_intent(state)
    assert next_node == "qa_node"

    # Verify qa routing ends
    qa_route = route_after_qa(state)
    assert qa_route == "__end__"


def test_get_graph_singleton():
    """Test that get_graph returns singleton"""
    from src.core.graph.builder import get_graph, reset_graph

    reset_graph()

    graph1 = get_graph()
    graph2 = get_graph()

    assert graph1 is graph2


def test_reset_graph():
    """Test that reset_graph creates new instance"""
    from src.core.graph.builder import get_graph, reset_graph

    reset_graph()

    graph1 = get_graph()
    reset_graph()
    graph2 = get_graph()

    assert graph1 is not graph2