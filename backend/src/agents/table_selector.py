"""
Table Selector - Layer 1
根据用户问题判断需要哪些表
"""
import re
from typing import List
from ..db.schema_loader import SchemaLoader
from ..core.llm import LLMClient, LLMError


class TableSelector:
    """表选择器"""

    SYSTEM_PROMPT = """你是一个 ERP 数据库专家。用户会提出查询需求，你需要判断需要查询哪些表。

只返回表名，用逗号分隔，不要其他内容。
如果不确定，返回最可能相关的表。

示例：
- 输入: "查员工信息" 输出: hr_employees
- 输入: "统计销售额" 输出: sal_orders, sal_order_items"""

    def __init__(self, schema_loader: SchemaLoader, llm_client: LLMClient):
        self.schema_loader = schema_loader
        self.llm_client = llm_client

    def select_tables(self, user_query: str, retry: int = 2) -> List[str]:
        """选择相关表"""
        table_summary = self.schema_loader.get_table_summary()

        user_prompt = f"""用户想要执行以下查询：
"{user_query}"

以下是 ERP 系统中的表及其描述：
{table_summary}

请判断用户可能需要查询哪些表，返回表名列表。只返回表名，用逗号分隔。"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        for attempt in range(retry):
            try:
                response = self.llm_client.chat(messages, temperature=0.1)
                tables = self._parse_response(response)
                if tables:
                    return tables
            except LLMError:
                if attempt == retry - 1:
                    return []

        return []

    def _parse_response(self, response: str) -> List[str]:
        """解析 LLM 返回的表名列表"""
        response = response.strip()
        parts = re.split(r'[,，、\n]', response)
        tables = []
        all_valid_tables = set(self.schema_loader.get_all_tables())

        for part in parts:
            part = part.strip()
            part = re.sub(r'^\d+[\.、]\s*', '', part)
            part = part.strip()

            if part and part in all_valid_tables:
                tables.append(part)

        return tables