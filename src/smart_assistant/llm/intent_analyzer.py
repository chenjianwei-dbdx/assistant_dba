"""
意图分析器模块
使用 LLM 分析用户输入的意图
"""
from typing import Dict, List, Optional
from .client import LLMClient
from .prompts import PromptManager
from ..tools.registry import ToolRegistry


class IntentAnalyzer:
    """意图分析器"""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        prompt_manager: PromptManager = None
    ):
        """
        初始化意图分析器

        Args:
            llm_client: LLM 客户端
            tool_registry: 工具注册表
            prompt_manager: 提示词管理器
        """
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.prompt_manager = prompt_manager or PromptManager()

    def analyze(self, user_input: str) -> Dict:
        """
        分析用户输入的意图

        Args:
            user_input: 用户输入

        Returns:
            意图分析结果，格式:
            {
                "intent": "tool_use" | "qa" | "unknown",
                "tool_name": str,
                "confidence": float,
                "reasoning": str,
                "extracted_params": dict,
                "missing_params": list
            }
        """
        # 获取工具定义
        tool_definitions = self.tool_registry.get_definitions_for_prompt()

        # 构建提示词
        prompt = self.prompt_manager.intent_analysis(
            tool_definitions=tool_definitions,
            user_input=user_input
        )

        # 调用 LLM
        try:
            response = self.llm_client.chat_with_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )

            # 验证和标准化结果
            return self._normalize_intent_result(response)

        except Exception as e:
            # LLM 调用失败，返回默认值
            return {
                "intent": "qa",
                "tool_name": None,
                "confidence": 0.0,
                "reasoning": f"Intent analysis failed: {str(e)}",
                "extracted_params": {},
                "missing_params": []
            }

    def extract_params(
        self,
        tool_name: str,
        collected_params: Dict,
        missing_params: List[str],
        user_input: str
    ) -> Dict:
        """
        提取工具参数

        Args:
            tool_name: 工具名称
            collected_params: 已收集的参数
            missing_params: 缺少的参数列表
            user_input: 用户输入

        Returns:
            参数提取结果:
            {
                "extracted": dict,
                "still_missing": list,
                "clarification_needed": str
            }
        """
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return {
                "extracted": {},
                "still_missing": missing_params,
                "clarification_needed": f"Tool {tool_name} not found"
            }

        definition = tool.definition

        # 格式化参数定义
        param_defs = self._format_param_definitions(definition.parameters)

        # 构建提示词
        prompt = self.prompt_manager.param_extraction(
            task_description=definition.description,
            tool_name=tool_name,
            param_definitions=param_defs,
            collected_params=collected_params,
            missing_params=missing_params,
            user_input=user_input
        )

        try:
            response = self.llm_client.chat_with_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )

            return {
                "extracted": response.get("extracted", {}),
                "still_missing": response.get("still_missing", []),
                "clarification_needed": response.get("clarification_needed", "")
            }

        except Exception as e:
            return {
                "extracted": {},
                "still_missing": missing_params,
                "clarification_needed": f"Parameter extraction failed: {str(e)}"
            }

    def generate_qa_response(
        self,
        conversation_history: List[Dict],
        user_input: str
    ) -> str:
        """
        生成问答回复

        Args:
            conversation_history: 对话历史
            user_input: 用户输入

        Returns:
            回复内容
        """
        history_str = self._format_conversation_history(conversation_history)

        prompt = self.prompt_manager.qa_response(
            conversation_history=history_str,
            user_input=user_input
        )

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response
        except Exception as e:
            return f"抱歉，生成回答时出错: {str(e)}"

    def summarize_tool_result(
        self,
        tool_result: Dict,
        user_request: str,
        tool_name: str
    ) -> str:
        """
        总结工具执行结果

        Args:
            tool_result: 工具执行结果
            user_request: 用户原始请求
            tool_name: 工具名称

        Returns:
            总结后的回复
        """
        prompt = self.prompt_manager.tool_result_summary(
            tool_result=str(tool_result),
            user_request=user_request,
            tool_name=tool_name
        )

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response
        except Exception as e:
            return f"工具执行完成，但生成总结时出错: {str(e)}"

    def _normalize_intent_result(self, result: Dict) -> Dict:
        """标准化意图分析结果"""
        return {
            "intent": result.get("intent", "unknown"),
            "tool_name": result.get("tool_name"),
            "confidence": float(result.get("confidence", 0.0)),
            "reasoning": result.get("reasoning", ""),
            "extracted_params": result.get("extracted_params", {}),
            "missing_params": result.get("missing_params", [])
        }

    def _format_param_definitions(self, parameters: List[Dict]) -> str:
        """格式化参数定义"""
        lines = []
        for p in parameters:
            name = p["name"]
            ptype = p.get("type", "string")
            required = "必填" if p.get("required", False) else "可选"
            description = p.get("description", "")
            enum = p.get("enum")
            default = p.get("default")

            line = f"- {name} ({ptype}, {required})"
            if enum:
                line += f"，可选值: {enum}"
            if default is not None:
                line += f"，默认值: {default}"
            line += f": {description}"

            lines.append(line)

        return "\n".join(lines)

    def _format_conversation_history(self, history: List[Dict]) -> str:
        """格式化对话历史"""
        if not history:
            return "（暂无历史对话）"

        lines = []
        for msg in history[-10:]:  # 最近 10 条
            role_map = {
                "user": "用户",
                "assistant": "助手",
                "system": "系统",
                "tool": "工具"
            }
            role = role_map.get(msg.get("role", ""), msg.get("role", ""))
            content = msg.get("content", "")
            # 截断过长内容
            if len(content) > 200:
                content = content[:200] + "..."
            lines.append(f"{role}: {content}")

        return "\n".join(lines)
