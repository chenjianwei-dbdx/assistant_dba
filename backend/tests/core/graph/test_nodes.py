"""Tests for LangGraph nodes"""
from unittest.mock import MagicMock, patch

import pytest


def test_intent_node_routes_qa():
    """Test intent_node when intent is qa"""
    from src.core.graph.nodes import intent_node

    state = {
        "messages": [{"role": "user", "content": "你好"}],
        "session_id": "test-123",
        "current_tool": None,
        "extracted_params": {},
        "missing_params": [],
        "intent_result": None,
        "tool_result": None,
        "error": None
    }

    mock_llm = MagicMock()
    mock_llm.chat.return_value = '{"intent": "qa", "tool_name": null, "confidence": 0.9}'

    config = {
        "configurable": {
            "llm_client": mock_llm,
            "tools": []
        }
    }

    result = intent_node(state, config)

    assert result["intent_result"]["intent"] == "qa"
    assert result["current_tool"] is None


def test_qa_node_returns_message():
    """Test qa_node returns assistant message"""
    from src.core.graph.nodes import qa_node

    state = {
        "messages": [{"role": "user", "content": "你好"}],
        "session_id": "test-123",
        "current_tool": None,
        "extracted_params": {},
        "missing_params": [],
        "intent_result": None,
        "tool_result": None,
        "error": None
    }

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "你好！有什么可以帮助你的吗？"

    config = {
        "configurable": {
            "llm_client": mock_llm
        }
    }

    result = qa_node(state, config)

    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["messages"][0]["role"] == "assistant"


def test_tool_node_no_tool():
    """Test tool_node when no tool specified"""
    from src.core.graph.nodes import tool_node

    state = {
        "messages": [{"role": "user", "content": "test"}],
        "session_id": "test-123",
        "current_tool": None,
        "extracted_params": {},
        "missing_params": [],
        "intent_result": None,
        "tool_result": None,
        "error": None
    }

    config = {"configurable": {}}

    result = tool_node(state, config)

    assert "error" in result
    assert "No tool specified" in result["error"]