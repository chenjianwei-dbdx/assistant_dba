"""
Chat Service
聊天服务层，整合 LLM 和工具调用
"""
import json
from typing import AsyncGenerator
from .llm import LLMClient, LLMError
from .intent import IntentAnalyzer
from ..plugins.registry import get_registry
from ..plugins.base import PluginContext
from ..db.database import get_default_manager


class ChatService:
    """聊天服务"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.registry = get_registry()
        # 注册所有内置插件
        from ..plugins.builtin import register_all
        register_all(self.registry)
        self.intent_analyzer = IntentAnalyzer(
            llm_client,
            self.registry.get_tools_prompt()
        )

    def process_message(self, message: str) -> dict:
        """处理消息，返回结构化结果"""
        # 意图分析
        intent = self.intent_analyzer.analyze(message)

        if intent["intent"] == "tool_use" and intent["tool_name"]:
            tool_name = intent["tool_name"]
            tool = self.registry.get(tool_name)

            if tool:
                params = intent.get("extracted_params", {})
                missing = intent.get("missing_params", [])

                if missing:
                    # 需要更多参数
                    return {
                        "type": "param_clarification",
                        "tool_name": tool_name,
                        "missing_params": missing,
                        "message": f"需要提供参数: {', '.join(missing)}"
                    }

                # 执行工具
                context = PluginContext(
                    db_manager=get_default_manager(),
                    llm_client=self.llm_client,
                    config={}
                )
                result = tool.execute(context, **params)
                return {
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error
                }

        elif intent["intent"] == "qa":
            # 直接回答
            response = self.llm_client.chat([
                {"role": "user", "content": message}
            ])
            return {
                "type": "qa",
                "message": response
            }

        else:
            return {
                "type": "unknown",
                "message": "抱歉，我无法理解您的请求"
            }

    def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """流式处理消息"""
        intent = self.intent_analyzer.analyze(message)

        if intent["intent"] == "tool_use" and intent["tool_name"]:
            tool_name = intent["tool_name"]
            tool = self.registry.get(tool_name)

            if tool:
                params = intent.get("extracted_params", {})
                missing = intent.get("missing_params", [])

                if missing:
                    yield json.dumps({
                        "type": "param_clarification",
                        "tool_name": tool_name,
                        "missing_params": missing
                    }, ensure_ascii=False)
                    return

                yield json.dumps({
                    "type": "tool_start",
                    "tool_name": tool_name
                }, ensure_ascii=False)

                context = PluginContext(
                    db_manager=get_default_manager(),
                    llm_client=self.llm_client,
                    config={}
                )
                result = tool.execute(context, **params)

                yield json.dumps({
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error
                }, ensure_ascii=False)
                return

        # 流式生成回答
        yield json.dumps({"type": "start"})
        try:
            for chunk in self.llm_client.chat_stream([
                {"role": "user", "content": message}
            ]):
                yield json.dumps({"type": "content", "content": chunk}, ensure_ascii=False)
        except LLMError as e:
            yield json.dumps({"type": "error", "error": str(e)})

        yield json.dumps({"type": "done"})
