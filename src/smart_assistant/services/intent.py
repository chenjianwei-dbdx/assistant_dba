"""
意图服务模块
封装意图分析器的服务
"""
from typing import Dict, List
from ..llm.client import LLMClient
from ..llm.intent_analyzer import IntentAnalyzer
from ..tools.registry import ToolRegistry


class IntentService:
    """意图服务"""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry
    ):
        """
        初始化意图服务

        Args:
            llm_client: LLM 客户端
            tool_registry: 工具注册表
        """
        self.llm_client = llm_client  # 公开给外部访问
        self.analyzer = IntentAnalyzer(llm_client, tool_registry)

    def analyze_intent(self, user_input: str) -> Dict:
        """
        分析用户意图

        Args:
            user_input: 用户输入

        Returns:
            意图分析结果
        """
        return self.analyzer.analyze(user_input)

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
            参数提取结果
        """
        return self.analyzer.extract_params(
            tool_name,
            collected_params,
            missing_params,
            user_input
        )

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
        return self.analyzer.generate_qa_response(
            conversation_history,
            user_input
        )

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
        return self.analyzer.summarize_tool_result(
            tool_result,
            user_request,
            tool_name
        )
