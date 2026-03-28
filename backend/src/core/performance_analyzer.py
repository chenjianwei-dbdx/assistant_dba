"""
Performance Analyzer
使用 LLM 分析数据库性能数据，生成优化建议
"""
from typing import Dict, Any, List
from ..core.llm import LLMClient


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
            # 清理思考标签
            import re
            clean_analysis = re.sub(r'<think>[\s\S]*?</think>', '', response)
            clean_analysis = re.sub(r'<think>.*$', '', clean_analysis, flags=re.MULTILINE).strip()

            return {
                "success": True,
                "suggestions": self._parse_suggestions(clean_analysis),
                "analysis": clean_analysis
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestions": [],
                "analysis": ""
            }

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
            for t in table_stats[:10]  # 只取前10个
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

请分析以上数据，用中文给出：
1. 当前数据库的整体健康状况评估
2. 具体的优化建议（针对发现的问题）
3. 需要立即处理的紧急问题

请用简洁的列表格式输出建议，每个建议说明：
- 问题是什么
- 如何解决（给出具体的 SQL 命令如果适用）

格式示例：
【健康评估】数据库整体状态：XXX
【紧急】问题1：XXX，建议：XXX
【建议】问题2：XXX，建议：XXX
"""

        return prompt

    def _parse_suggestions(self, response: str) -> List[Dict[str, str]]:
        """从 AI 响应中解析建议"""
        # 移除扩展思考标签及其内容
        import re
        clean_response = re.sub(r'<think>[\s\S]*?</think>', '', response)
        # 移除 <think> 开头的思考内容（如果没有结束标签）
        clean_response = re.sub(r'<think>.*$', '', clean_response, flags=re.MULTILINE)

        suggestions = []
        lines = clean_response.split("\n")
        current_priority = "建议"

        for line in lines:
            line = line.strip()
            if "【紧急】" in line or "【严重】" in line:
                current_priority = "紧急"
                line = line.replace("【紧急】", "").replace("【严重】", "").strip()
            elif "【警告】" in line or "【注意】" in line:
                current_priority = "警告"
                line = line.replace("【警告】", "").replace("【注意】", "").strip()
            elif "【建议】" in line or "【优化】" in line:
                current_priority = "建议"
                line = line.replace("【建议】", "").replace("【优化】", "").strip()
            elif "【健康评估】" in line or "【评估】" in line or "【总结】" in line:
                continue  # 健康评估不是建议

            # 过滤掉表格行、空行、过于简短的行
            if line and len(line) > 10 and not line.startswith("|") and not line.startswith("-"):
                suggestions.append({
                    "priority": current_priority,
                    "text": line
                })

        return suggestions[:10]  # 最多返回10条建议
