"""Tests for LangGraph edges"""
import pytest


def test_route_after_intent_tool_use_with_params():
    """Test routing when intent is tool_use and params complete"""
    from src.core.graph.edges import route_after_intent

    state = {
        "intent_result": {
            "intent": "tool_use",
            "tool_name": "query_executor",
            "missing_params": []
        }
    }

    result = route_after_intent(state)
    assert result == "tool_node"


def test_route_after_intent_tool_use_missing_params():
    """Test routing when intent is tool_use but params missing"""
    from src.core.graph.edges import route_after_intent

    state = {
        "intent_result": {
            "intent": "tool_use",
            "tool_name": "slow_query_analyzer",
            "missing_params": ["connection_id"]
        }
    }

    result = route_after_intent(state)
    assert result == "clarification_node"


def test_route_after_intent_qa():
    """Test routing when intent is qa"""
    from src.core.graph.edges import route_after_intent

    state = {
        "intent_result": {
            "intent": "qa",
            "tool_name": None,
            "missing_params": []
        }
    }

    result = route_after_intent(state)
    assert result == "qa_node"


def test_route_after_intent_unknown():
    """Test routing when intent is unknown"""
    from src.core.graph.edges import route_after_intent

    state = {
        "intent_result": {
            "intent": "unknown",
            "tool_name": None,
            "missing_params": []
        }
    }

    result = route_after_intent(state)
    assert result == "qa_node"


def test_route_after_tool():
    """Test that tool_node routes to __end__"""
    from src.core.graph.edges import route_after_tool

    state = {"tool_result": {"success": True}}
    result = route_after_tool(state)
    assert result == "__end__"


def test_route_after_qa():
    """Test that qa_node routes to __end__"""
    from src.core.graph.edges import route_after_qa

    state = {}
    result = route_after_qa(state)
    assert result == "__end__"


def test_route_after_clarification():
    """Test that clarification_node routes back to intent_node"""
    from src.core.graph.edges import route_after_clarification

    state = {}
    result = route_after_clarification(state)
    assert result == "intent_node"