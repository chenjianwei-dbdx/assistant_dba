"""
SQL Template API
SQL 模板管理接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from src.core.dependencies import get_template_manager
from src.db.connection import get_monitor_connection

router = APIRouter()


class TemplateCreate(BaseModel):
    name: str
    category: str
    description: str = ""
    sql_pattern: str
    parameters: List[dict] = []
    examples: str = ""


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    sql_pattern: Optional[str] = None
    parameters: Optional[List[dict]] = None
    examples: Optional[str] = None
    is_favorite: Optional[bool] = None


class TemplateExecute(BaseModel):
    template_id: int
    params: dict = {}


@router.get("/templates")
async def list_templates(category: str = None, keyword: str = None):
    """列出所有模板"""
    manager = get_template_manager()
    templates = manager.list_templates(category=category, keyword=keyword)
    return {
        "templates": [t.to_dict() for t in templates],
        "categories": manager.list_categories()
    }


@router.get("/templates/categories")
async def list_categories():
    """列出所有分类"""
    manager = get_template_manager()
    return {"categories": manager.list_categories()}


@router.get("/templates/{template_id}")
async def get_template(template_id: int):
    """获取单个模板"""
    manager = get_template_manager()
    template = manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()


@router.post("/templates")
async def create_template(data: TemplateCreate):
    """创建模板"""
    manager = get_template_manager()
    template = manager.add_template(data.model_dump())
    return template.to_dict()


@router.put("/templates/{template_id}")
async def update_template(template_id: int, data: TemplateUpdate):
    """更新模板"""
    manager = get_template_manager()
    template = manager.update_template(template_id, data.model_dump(exclude_none=True))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int):
    """删除模板"""
    manager = get_template_manager()
    if not manager.delete_template(template_id):
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True}


@router.post("/templates/execute")
async def execute_template(data: TemplateExecute):
    """执行模板 SQL"""
    manager = get_template_manager()
    template = manager.get_template(data.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # 填充参数（使用模板中定义的默认值）
    sql = manager.fill_parameters(template.sql_pattern, data.params, template.parameters)

    try:
        conn = get_monitor_connection()
        cur = conn.cursor()
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # 增加使用次数
        manager.increment_use_count(data.template_id)

        return {
            "success": True,
            "columns": columns,
            "rows": [dict(zip(columns, row)) for row in rows],
            "row_count": len(rows),
            "template_name": template.name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/templates/match")
async def match_template(query: str):
    """匹配模板（基于关键词）"""
    manager = get_template_manager()
    templates = manager.list_templates()

    # 简单的关键词匹配
    query_lower = query.lower()
    matched = []

    for t in templates:
        score = 0
        # 名称匹配
        if any(kw in t.name.lower() for kw in query_lower.split()):
            score += 3
        # 描述匹配
        if any(kw in t.description.lower() for kw in query_lower.split()):
            score += 2
        # 示例匹配
        if any(kw in t.examples.lower() for kw in query_lower.split()):
            score += 1

        if score > 0:
            matched.append({
                "template": t.to_dict(),
                "score": score
            })

    # 按分数排序
    matched.sort(key=lambda x: x["score"], reverse=True)

    return {
        "matches": matched[:5],  # 返回前 5 个匹配
        "query": query
    }
