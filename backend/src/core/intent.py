"""
Intent Analyzer Module
意图分析模块
"""
from typing import Dict, List
from .llm import LLMClient


class IntentAnalyzer:
    """意图分析器"""

    def __init__(self, llm_client: LLMClient, tools_prompt: str):
        self.llm_client = llm_client
        self.tools_prompt = tools_prompt

    def analyze(self, user_input: str) -> Dict:
        """分析用户意图"""
        prompt = f"""你是一个数据库助手，需要分析用户意图并选择合适的工具。

可用工具：
{self.tools_prompt}

用户输入：{user_input}

请以 JSON 格式输出分析结果：
{{
    "intent": "tool_use" | "qa" | "unknown",
    "tool_name": "工具名称（仅当 intent=tool_use 时）",
    "confidence": 0.0-1.0,
    "reasoning": "分析理由",
    "extracted_params": {{ "参数名": "值" }},
    "missing_params": ["缺少的参数"]
}}

请直接输出 JSON，不要有其他内容。"""

        try:
            response = self.llm_client.chat_with_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return self._normalize_result(response)
        except Exception as e:
            import logging
            logging.warning(f"Intent analysis failed: {e}, falling back to qa")
            return {
                "intent": "qa",
                "tool_name": None,
                "confidence": 0.0,
                "reasoning": f"分析失败: {str(e)}",
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
        """提取工具参数"""
        prompt = f"""提取参数：
工具：{tool_name}
已收集参数：{collected_params}
缺少参数：{missing_params}
用户输入：{user_input}

请输出 JSON：
{{
    "extracted": {{ "参数名": "值" }},
    "still_missing": ["仍未提供的参数"],
    "clarification_needed": "需要澄清的问题"
}}"""

        try:
            return self.llm_client.chat_with_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
        except Exception:
            return {
                "extracted": {},
                "still_missing": missing_params,
                "clarification_needed": ""
            }

    def _normalize_result(self, result: Dict) -> Dict:
        """标准化结果"""
        return {
            "intent": result.get("intent", "unknown"),
            "tool_name": result.get("tool_name"),
            "confidence": float(result.get("confidence", 0.0)),
            "reasoning": result.get("reasoning", ""),
            "extracted_params": result.get("extracted_params", {}),
            "missing_params": result.get("missing_params", [])
        }
