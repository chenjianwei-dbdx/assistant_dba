"""
Template Matching Logic
模板匹配逻辑
"""
from typing import List, Dict, Any, Optional
from ...core.dependencies import get_template_manager, TemplateManager


# 元查询模式 - 查询数据库结构的特殊查询
META_PATTERNS = [
    '有哪些表', '所有表', '表有哪些', '查询表', 'show tables',
    '有什么表', '库里有', '数据库结构', '所有表名',
    '表的列表', 'list tables'
]

# Category 关键词映射
CATEGORY_KEYWORDS = {
    'performance': ['性能', '慢', '耗时', 'cpu', 'performance', '慢查询', '执行时间', 'top sql'],
    'slow_query': ['慢查询', '慢', '耗时', '执行时间', 'slow query'],
    'deadlock': ['死锁', 'deadlock', '阻塞', 'lock'],
    'index_stats': ['索引', 'index', '索引膨胀', '未使用索引', 'idx'],
    'table_stats': ['表', '表大小', '空间', '占用', '表空间', '排行'],
    'vacuum': ['vacuum', '垃圾', '死亡元组', '清理', 'dead tuple'],
    'connection': ['连接', '连接数', 'session', '活跃连接', '长事务', '并发'],
    'database': ['数据库', '统计', '概览', 'database', 'db', '健康']
}


def is_meta_query(query: str) -> bool:
    """判断是否为元查询（查询数据库结构）"""
    query_lower = query.lower()
    return any(p in query_lower for p in META_PATTERNS)


def calculate_template_score(template, query_lower: str) -> int:
    """计算模板与查询的匹配分数

    Args:
        template: SQLTemplate 实例
        query_lower: 小写化的查询字符串

    Returns:
        匹配分数，>=3分才算匹配
    """
    score = 0
    keywords = query_lower.split()

    # 名称匹配 (最高优先级)
    if any(kw in template.name.lower() for kw in keywords):
        score += 5

    # 描述匹配
    if any(kw in template.description.lower() for kw in keywords):
        score += 3

    # 示例匹配
    if any(kw in template.examples.lower() for kw in keywords):
        score += 2

    # category 关键词匹配
    if template.category in CATEGORY_KEYWORDS:
        category_keywords = CATEGORY_KEYWORDS[template.category]
        if any(kw in query_lower for kw in category_keywords):
            score += 3

    return score


def match_templates(query: str, threshold: int = 3) -> List[Dict[str, Any]]:
    """匹配查询与模板

    Args:
        query: 用户查询
        threshold: 最低匹配分数阈值（默认3分）

    Returns:
        匹配的模板列表，按分数降序排列
    """
    manager = get_template_manager()
    templates = manager.list_templates()
    query_lower = query.lower()
    matched = []

    for t in templates:
        score = calculate_template_score(t, query_lower)
        if score >= threshold:
            matched.append({
                "template": t.to_dict(),
                "score": score
            })

    # 按分数排序
    matched.sort(key=lambda x: x["score"], reverse=True)
    return matched


def get_best_template_match(query: str) -> Optional[Dict[str, Any]]:
    """获取最佳匹配的模板

    Args:
        query: 用户查询

    Returns:
        最佳匹配的模板信息，如果没有匹配返回 None
    """
    matched = match_templates(query)
    return matched[0] if matched else None
