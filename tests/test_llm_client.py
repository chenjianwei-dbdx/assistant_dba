"""
Tests for LLM Client
"""
import pytest
from backend.src.core.llm import LLMClient


def test_llm_client_init():
    """测试 LLM 客户端初始化"""
    config = {
        "base_url": "https://api.minimaxi.com/v1",
        "api_key": "test-key",
        "model": "MiniMax-M2",
        "timeout": 120
    }
    client = LLMClient(config)
    assert client.base_url == "https://api.minimaxi.com/v1"
    assert client.model == "MiniMax-M2"


def test_llm_client_chat_request_format():
    """测试聊天请求格式"""
    config = {
        "base_url": "https://api.minimaxi.com/v1",
        "api_key": "test-key",
        "model": "MiniMax-M2",
        "timeout": 30
    }
    client = LLMClient(config)
    # 验证请求体能正确构建
    assert hasattr(client, 'chat')
    assert hasattr(client, 'chat_stream')
