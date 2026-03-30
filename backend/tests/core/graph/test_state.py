"""Tests for ConversationState"""
import pytest
from datetime import datetime


def test_conversation_state_initialization():
    from src.core.graph.state import ConversationState

    state = ConversationState(
        messages=[],
        session_id=None,
        current_tool=None,
        extracted_params={},
        missing_params=[],
        intent_result=None,
        tool_result=None,
        error=None
    )
    assert state["messages"] == []
    assert state["session_id"] is None
    assert state["current_tool"] is None
    assert state["extracted_params"] == {}


def test_message_creation():
    from src.core.graph.state import Message

    msg = Message(
        role="user",
        content="hello",
        tool_name=None,
        tool_result=None,
        timestamp=datetime.now()
    )
    assert msg["role"] == "user"
    assert msg["content"] == "hello"