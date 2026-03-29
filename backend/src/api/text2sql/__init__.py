"""
Text2SQL Package
自然语言转 SQL 包

子模块:
- generate: NL → SQL 生成逻辑
- explain: SQL 执行与 EXPLAIN 逻辑
- templates: 模板匹配逻辑
"""
from .generate import generate_sql
from .explain import execute_sql, explain_sql

__all__ = ['generate_sql', 'execute_sql', 'explain_sql']
