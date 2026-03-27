"""
SQL Generator - Layer 2
根据用户问题和表结构生成 SQL
"""
import re
from typing import Dict, Optional, Tuple
from ..db.schema_loader import SchemaLoader
from ..db.schema_introspector import SchemaIntrospector
from ..core.llm import LLMClient, LLMError


class SQLGenerator:
    """SQL 生成器"""

    SYSTEM_PROMPT = """你是一个 ERP 数据库专家，擅长根据用户需求生成 PostgreSQL SQL。

要求：
1. 只生成 SELECT 查询，禁止 INSERT/UPDATE/DELETE/DROP 等操作
2. 使用正确的 PostgreSQL 语法
3. 表名和列名使用实际名称，不要臆造
4. 如果需要 JOIN，确保外键关系正确

请按以下格式返回：
SQL: <生成的 SQL 语句>
解释: <SQL 的简要说明>

注意：只返回 SQL 和解释，不要其他内容。"""

    def __init__(self, schema_loader: SchemaLoader, introspector: SchemaIntrospector, llm_client: LLMClient):
        self.schema_loader = schema_loader
        self.introspector = introspector
        self.llm_client = llm_client

    def generate(self, user_query: str, table_names: list, retry: int = 2) -> Tuple[str, str]:
        """生成 SQL"""
        table_details = self.schema_loader.get_table_details(table_names, self.introspector)

        user_prompt = f"""用户想要查询：
"{user_query}"

请根据以下表结构生成 SQL：

{table_details}

要求：只生成 SELECT 查询，使用正确的 PostgreSQL 语法。

请按以下格式返回：
SQL: <SQL 语句>
解释: <简要说明>"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        for attempt in range(retry):
            try:
                response = self.llm_client.chat(messages, temperature=0.1)
                return self._parse_response(response)
            except LLMError:
                if attempt == retry - 1:
                    return "", "AI 生成失败，请重试或手动输入 SQL"

        return "", "AI 生成失败，请重试或手动输入 SQL"

    def _parse_response(self, response: str) -> Tuple[str, str]:
        """解析 LLM 返回的 SQL 和解释"""
        response = response.strip()

        sql_match = re.search(r'SQL:\s*(.+?)(?=解释:|$)', response, re.DOTALL | re.IGNORECASE)
        sql = sql_match.group(1).strip() if sql_match else ""

        exp_match = re.search(r'解释:\s*(.+?)(?=$)', response, re.DOTALL | re.IGNORECASE)
        explanation = exp_match.group(1).strip() if exp_match else ""

        sql = sql.strip()
        if sql and not sql.endswith(';'):
            sql = sql + ';'

        return sql, explanation