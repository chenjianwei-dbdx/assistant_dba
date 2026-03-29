"""
Performance Analyzer
使用 LLM 分析数据库性能数据，生成优化建议
"""
from typing import Dict, Any, List
from ..core.llm import LLMClient
import json
import re


class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def analyze(self, overview: Dict[str, Any], table_stats: List[Dict], index_stats: List[Dict] = None) -> Dict[str, Any]:
        """
        分析性能数据，生成优化建议

        Args:
            overview: 概览数据 (connections, active_queries, hit_rate, etc.)
            table_stats: 表统计列表
            index_stats: 索引统计列表（可选）

        Returns:
            包含分析结果的字典
        """
        prompt = self._build_prompt(overview, table_stats, index_stats)

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            # 先尝试提取 JSON 部分
            suggestions = self._extract_json_suggestions(response)
            clean_analysis = self._clean_analysis_text(response)

            return {
                "success": True,
                "suggestions": suggestions,
                "analysis": clean_analysis
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestions": [],
                "analysis": ""
            }

    def _extract_json_suggestions(self, response: str) -> List[Dict[str, str]]:
        """从 AI 响应中提取结构化建议"""
        # 移除思考标签
        clean = re.sub(r'<think>[\s\S]*?</think>', '', response)
        clean = re.sub(r'<think>[\s\S]*?</think>', '', clean)  # 清理 MiniMax 扩展思考标签
        clean = re.sub(r'<think>.*$', '', clean, flags=re.MULTILINE)  # 清理单行思考标签

        # 尝试提取 JSON
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', clean)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if isinstance(data, list):
                    return data[:10]
                elif isinstance(data, dict) and "suggestions" in data:
                    return data["suggestions"][:10]
            except json.JSONDecodeError:
                pass

        # 如果没有 JSON，从代码块提取 SQL 作为建议
        return self._extract_sql_suggestions(clean)

    def _extract_sql_suggestions(self, response: str) -> List[Dict[str, str]]:
        """从 Markdown 中提取 SQL 语句作为建议"""
        suggestions = []

        # 从代码块中提取所有 SQL
        sql_lines = []
        code_blocks = re.findall(r'```(?:sql)?\s*([\s\S]*?)\s*```', response, re.IGNORECASE)
        for block in code_blocks:
            for line in block.split('\n'):
                line = line.strip()
                # 跳过注释和空行
                if line and not line.startswith('--') and len(line) > 8:
                    line = re.sub(r'^\-\-\s*', '', line)
                    line = line.rstrip(';').strip()
                    if self._looks_like_sql(line):
                        sql_lines.append(line)

        # 去重
        seen = set()
        unique_sqls = []
        for sql in sql_lines:
            sql_lower = sql.lower()
            if sql_lower not in seen:
                seen.add(sql_lower)
                unique_sqls.append(sql)

        # 为每个唯一 SQL 创建建议
        for sql in unique_sqls[:8]:
            # 确定优先级
            priority = "建议"
            sql_upper = sql.upper()
            if 'VACUUM' in sql_upper:
                priority = "紧急"
                text = f"执行 VACUUM 清理死亡元组"
            elif 'CREATE INDEX' in sql_upper:
                priority = "警告"
                text = f"创建索引优化查询性能"
            elif 'ALTER' in sql_upper:
                priority = "建议"
                text = f"修改表结构"
            else:
                text = sql[:60] + ("..." if len(sql) > 60 else "")

            suggestions.append({
                "priority": priority,
                "text": text,
                "sql": sql + ";"
            })

        return suggestions

    def _looks_like_sql(self, text: str) -> bool:
        """判断文本是否像 SQL"""
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'VACUUM', 'ANALYZE', 'INDEX', 'TABLE', 'GRANT', 'REINDEX']
        text_upper = text.upper()
        return any(text_upper.startswith(kw) or text_upper.startswith(kw + ' ') for kw in sql_keywords)

    def _clean_analysis_text(self, response: str) -> str:
        """清理分析文本，移除思考标签"""
        clean = re.sub(r'<think>[\s\S]*?</think>', '', response)
        clean = re.sub(r'<think>[\s\S]*?</think>', '', clean)  # 清理 MiniMax 扩展思考标签
        clean = re.sub(r'<think>.*$', '', clean, flags=re.MULTILINE)  # 清理单行思考标签
        return clean.strip()

    def _build_prompt(self, overview: Dict, table_stats: List[Dict], index_stats: List[Dict] = None) -> str:
        """构建分析提示词"""
        hit_rate = overview.get("hit_rate", "0")
        connections = overview.get("connections", 0)
        active_queries = overview.get("active_queries", 0)
        commit = overview.get("commit", 0)
        rollback = overview.get("rollback", 0)

        # 找出问题最严重的表
        problem_tables = []
        for t in table_stats:
            dead_rows = t.get("dead_rows", 0)
            seq_scans = t.get("seq_scans", 0)
            idx_scans = t.get("index_scans", 0)
            total_scans = seq_scans + idx_scans
            idx_ratio = (idx_scans / total_scans * 100) if total_scans > 0 else 0

            if dead_rows > 100:
                problem_tables.append({
                    "table": t.get("table", ""),
                    "dead_rows": dead_rows,
                    "reason": "死亡元组过多"
                })
            if idx_ratio < 50 and seq_scans > 1000:
                problem_tables.append({
                    "table": t.get("table", ""),
                    "seq_scans": seq_scans,
                    "idx_ratio": round(idx_ratio, 1),
                    "reason": "索引扫描率过低，全表扫描过多"
                })

        tables_text = "\n".join([
            f"- {t['table']}: 死亡行={t.get('dead_rows', 0)}, "
            f"全表扫描={t.get('seq_scans', 0)}, 索引扫描={t.get('index_scans', 0)}, "
            f"插入={t.get('inserts', 0)}, 更新={t.get('updates', 0)}, 删除={t.get('deletes', 0)}"
            for t in table_stats[:10]
        ])

        problem_text = "\n".join([
            f"- {p['table']}: {p['reason']}"
            for p in problem_tables[:5]
        ]) if problem_tables else "无明显问题的表"

        prompt = f"""你是一个 PostgreSQL DBA 专家，请分析以下数据库性能数据并给出优化建议。

## 数据库概览
- 当前连接数: {connections}
- 活跃查询数: {active_queries}
- 缓存命中率: {hit_rate}%
- 事务提交/回滚: {commit} / {rollback}

## 表扫描统计（前10个表）
{tables_text}

## 重点问题表
{problem_text if problem_text else "无"}

请分析以上数据，先给出健康评估，然后给出具体优化建议。

【重要】请以 JSON 格式返回建议列表，格式如下：
```json
[
  {{
    "priority": "紧急",
    "text": "问题描述：XXX，建议：执行 VACUUM ANALYZE 清理死亡元组",
    "sql": "VACUUM ANALYZE hr_employees;"
  }},
  {{
    "priority": "建议",
    "text": "问题描述：XXX，建议：创建索引",
    "sql": "CREATE INDEX CONCURRENTLY idx_hr_employees_dept ON hr_employees(department_id);"
  }}
]
```

注意：
1. priority 可选值：紧急、警告、建议
2. sql 字段：如果该建议有对应的 SQL 命令则填写，如果没有则填空字符串 ""
3. 只返回真正需要执行的 SQL，不要编造不需要执行的 SQL
4. 最多返回 8 条建议

现在请分析并返回 JSON：
"""

        return prompt
