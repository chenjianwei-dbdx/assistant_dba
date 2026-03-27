"""
Result Summarizer - Layer 3
对查询结果进行 AI 摘要
"""
from typing import List, Dict, Any
from ..core.llm import LLMClient, LLMError


class ResultSummarizer:
    """结果摘要生成器"""

    SYSTEM_PROMPT = """你是一个数据分析专家，擅长解读数据库查询结果。

请用 2-3 句话总结这批数据的主要发现和含义。语言要简洁专业。"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def summarize(self, columns: List[str], rows: List[Dict[str, Any]], retry: int = 2) -> str:
        """生成结果摘要"""
        if not rows:
            return "查询结果为空"

        # 限制数据量
        display_rows = rows[:10]
        row_count = len(rows)

        # 格式化数据
        data_lines = []
        for row in display_rows:
            data_lines.append(str(row))

        user_prompt = f"""查询结果（共 {row_count} 行）：
列名：{', '.join(columns)}

数据示例：
{chr(10).join(data_lines)}

请用 2-3 句话总结这批数据的主要发现和含义。"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        for attempt in range(retry):
            try:
                summary = self.llm_client.chat(messages, temperature=0.3)
                return summary.strip()
            except LLMError:
                if attempt == retry - 1:
                    return ""

        return ""