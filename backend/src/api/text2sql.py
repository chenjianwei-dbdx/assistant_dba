"""
Text2SQL API
自然语言转 SQL 的 API 端点
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import time

from ..db.schema_loader import SchemaLoader
from ..db.schema_introspector import SchemaIntrospector
from ..db.sql_validator import SQLValidator
from ..agents.table_selector import TableSelector
from ..agents.sql_generator import SQLGenerator
from ..agents.result_summarizer import ResultSummarizer
from ..core.llm import LLMClient, LLMError

router = APIRouter()


class Text2SQLRequest(BaseModel):
    connection_id: str
    query: str


class Text2SQLExecuteRequest(BaseModel):
    connection_id: str
    sql: str


class Text2SQLResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端"""
    import yaml
    with open('/Users/cjwdsg/smart-assistant/configs/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    llm_config = config.get('llm', {})
    return LLMClient(llm_config)


def get_schema_loader() -> SchemaLoader:
    """获取 Schema 加载器"""
    return SchemaLoader()


def get_introspector() -> SchemaIntrospector:
    """获取 Schema Introspector"""
    from sqlalchemy import create_engine
    engine = create_engine(
        "postgresql://cjwdsg:@127.0.0.1:5432/erp_simulation"
    )
    return SchemaIntrospector(engine)


@router.post("/text2sql")
async def generate_sql(req: Text2SQLRequest) -> Text2SQLResponse:
    """Text2SQL：生成 SQL"""
    try:
        schema_loader = get_schema_loader()

        # 特殊处理：元查询（查询数据库结构）
        meta_patterns = [
            '有哪些表', '所有表', '表有哪些', '查询表', 'show tables',
            '有什么表', '库里有', '数据库结构', '所有表名',
            '表的列表', 'list tables'
        ]
        is_meta_query = any(p in req.query.lower() for p in meta_patterns)

        if is_meta_query:
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

            return Text2SQLResponse(
                success=True,
                data={
                    "sql": "",  # 无需 SQL
                    "explanation": f"数据库中共有 {len(tables_with_desc)} 张表，均为 ERP 业务表",
                    "affected_tables": all_tables,
                    "is_meta_query": True,
                    "tables": tables_with_desc,
                    "estimated_rows": len(tables_with_desc)
                }
            )

        introspector = get_introspector()
        llm_client = get_llm_client()

        # Layer 1: 表选择
        table_selector = TableSelector(schema_loader, llm_client)
        selected_tables = table_selector.select_tables(req.query)

        if not selected_tables:
            return Text2SQLResponse(
                success=False,
                error="无法确定相关的表，请尝试更详细的描述"
            )

        # Layer 2: SQL 生成
        sql_generator = SQLGenerator(schema_loader, introspector, llm_client)
        sql, explanation = sql_generator.generate(req.query, selected_tables)

        if not sql:
            return Text2SQLResponse(
                success=False,
                error=explanation or "SQL 生成失败"
            )

        # 验证 SQL
        validator = SQLValidator()
        valid_tables = schema_loader.get_all_tables()
        validation = validator.validate(sql, valid_tables)

        if not validation.valid:
            return Text2SQLResponse(
                success=False,
                error=validation.error
            )

        return Text2SQLResponse(
            success=True,
            data={
                "sql": sql,
                "explanation": explanation,
                "affected_tables": selected_tables,
                "estimated_rows": 10
            }
        )

    except LLMError as e:
        return Text2SQLResponse(
            success=False,
            error=f"AI 服务错误: {str(e)}"
        )
    except Exception as e:
        return Text2SQLResponse(
            success=False,
            error=f"服务器错误: {str(e)}"
        )


@router.post("/text2sql/execute")
async def execute_sql(req: Text2SQLExecuteRequest) -> Text2SQLResponse:
    """Text2SQL：执行 SQL"""
    try:
        schema_loader = get_schema_loader()
        validator = SQLValidator()
        valid_tables = schema_loader.get_all_tables()
        validation = validator.validate(req.sql, valid_tables)

        if not validation.valid:
            return Text2SQLResponse(
                success=False,
                error=validation.error
            )

        from sqlalchemy import create_engine, text

        engine = create_engine(
            "postgresql://cjwdsg:@127.0.0.1:5432/erp_simulation"
        )

        start_time = time.time()
        with engine.connect() as conn:
            result = conn.execute(text(req.sql))
            rows = result.fetchmany(1000)
            columns = list(result.keys())
            execution_time_ms = int((time.time() - start_time) * 1000)

        row_dicts = [dict(zip(columns, row)) for row in rows]

        # Layer 3: 结果摘要
        llm_client = get_llm_client()
        summarizer = ResultSummarizer(llm_client)
        summary = summarizer.summarize(columns, row_dicts)

        return Text2SQLResponse(
            success=True,
            data={
                "columns": columns,
                "rows": row_dicts,
                "row_count": len(row_dicts),
                "execution_time_ms": execution_time_ms,
                "summary": summary
            }
        )

    except Exception as e:
        return Text2SQLResponse(
            success=False,
            error=f"执行错误: {str(e)}"
        )