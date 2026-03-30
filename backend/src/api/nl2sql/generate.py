"""
NL → SQL Generation Logic
自然语言转 SQL 生成逻辑
"""
from typing import Optional, Tuple
from ...db.schema_loader import SchemaLoader
from ...db.schema_introspector import SchemaIntrospector
from ...db.sql_validator import SQLValidator
from ...agents.table_selector import TableSelector
from ...agents.sql_generator import SQLGenerator
from ...core.llm import LLMClient, LLMError
from .templates import is_meta_query, get_best_template_match


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端"""
    from src.config import get_config
    config = get_config()
    llm_config = config.get('llm', {})
    return LLMClient(llm_config)


def get_schema_loader() -> SchemaLoader:
    """获取 Schema 加载器"""
    return SchemaLoader()


def get_introspector() -> SchemaIntrospector:
    """获取 Schema Introspector"""
    from sqlalchemy import create_engine
    from src.config import get_config
    config = get_config()
    monitor = config.get("monitor", {})
    db = config.get("database", {})
    host = monitor.get("host", db.get("host", "127.0.0.1"))
    port = monitor.get("port", db.get("port", 5432))
    user = monitor.get("username", db.get("username", "cjwdsg"))
    password = monitor.get("password", db.get("password", ""))
    database = monitor.get("database", db.get("database", "erp_simulation"))
    conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(conn_str)
    return SchemaIntrospector(engine)


def generate_sql(connection_id: str, query: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """生成 SQL 的主逻辑

    Args:
        connection_id: 数据库连接 ID
        query: 用户查询（自然语言）

    Returns:
        Tuple of (success, data, error)
        - success: 是否成功
        - data: 成功时返回的数据字典
        - error: 失败时返回的错误信息
    """
    schema_loader = get_schema_loader()

    # ========== 优先匹配模板 ==========
    if not is_meta_query(query):
        best_match = get_best_template_match(query)
        if best_match:
            return True, {
                "sql": "",  # 模板不需要生成SQL
                "explanation": f"根据您的查询，已匹配模板：{best_match['template']['name']}",
                "matched_template": best_match["template"],
                "template_score": best_match["score"],
                "is_template_match": True,
                "estimated_rows": 10
            }, None
    # ========== 模板匹配结束 ==========

    if is_meta_query(query):
        # 直接返回表列表，不生成 SQL
        all_tables = schema_loader.get_all_tables()
        tables_with_desc = []
        for table_name in all_tables:
            config = schema_loader.get_table_config(table_name)
            if config:
                tables_with_desc.append({
                    "name": table_name,
                    "module": config.get('module', ''),
                    "description": config.get('description', '')
                })

        return True, {
            "sql": "",  # 无需 SQL
            "explanation": f"数据库中共有 {len(tables_with_desc)} 张表，均为 ERP 业务表",
            "affected_tables": all_tables,
            "is_meta_query": True,
            "tables": tables_with_desc,
            "estimated_rows": len(tables_with_desc)
        }, None

    introspector = get_introspector()
    llm_client = get_llm_client()

    # Layer 1: 表选择
    table_selector = TableSelector(schema_loader, llm_client)
    selected_tables = table_selector.select_tables(query)

    if not selected_tables:
        return False, None, "无法确定相关的表，请尝试更详细的描述"

    # Layer 2: SQL 生成
    sql_generator = SQLGenerator(schema_loader, introspector, llm_client)
    sql, explanation = sql_generator.generate(query, selected_tables)

    if not sql:
        return False, None, explanation or "SQL 生成失败"

    # 验证 SQL
    validator = SQLValidator()
    valid_tables = schema_loader.get_all_tables()
    validation = validator.validate(sql, valid_tables)

    if not validation.valid:
        return False, None, validation.error

    return True, {
        "sql": sql,
        "explanation": explanation,
        "affected_tables": selected_tables,
        "estimated_rows": 10
    }, None
