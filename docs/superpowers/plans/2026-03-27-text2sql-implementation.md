# Text2SQL 智能查询系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 SQL 查询页面嵌入 AI 能力，通过自然语言描述自动生成 SQL 查询语句

**Architecture:** 三层 LLM 架构（表选择 → SQL 生成 → 结果摘要），RAG 模式加载表结构，用户确认后执行

**Tech Stack:** Python (FastAPI backend), React/TypeScript (Frontend), MiniMax M2.7 (LLM), PostgreSQL

---

## 文件结构

```
configs/
├── erp_schema.json              # 表结构配置（新建）
backend/src/
├── db/
│   ├── schema_loader.py          # Schema 读取器（新建）
│   ├── schema_introspector.py    # 已有，动态获取字段
│   └── sql_validator.py          # SQL 验证层（新建）
├── agents/
│   ├── table_selector.py         # Layer 1 表选择（新建）
│   ├── sql_generator.py          # Layer 2 SQL 生成（新建）
│   └── result_summarizer.py      # Layer 3 结果摘要（新建）
├── api/
│   └── text2sql.py               # Text2SQL API（新建）
frontend/src/pages/
└── Query/
    └── index.tsx                 # 修改，AI 辅助界面
```

---

## Task 1: 创建 erp_schema.json 表结构配置

**Files:**
- Create: `configs/erp_schema.json`

首先需要从数据库获取所有表名和结构：

```bash
# 获取 erp_simulation 数据库所有表
psql -h 127.0.0.1 -U cjwdsg -d erp_simulation -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;"
```

- [ ] **Step 1: 创建 erp_schema.json**

```json
{
  "version": "1.0",
  "description": "ERP 仿真数据库 Schema 配置",
  "modules": ["HR", "CRM", "SCM", "INV", "PUR", "SAL", "FIN", "PRO", "MRP", "SYS", "WMS"],
  "tables": [
    {
      "name": "hr_departments",
      "module": "HR",
      "tags": ["部门", "组织架构", "人力资源"],
      "description": "部门表，记录公司组织结构"
    },
    {
      "name": "hr_positions",
      "module": "HR",
      "tags": ["岗位", "职位", "人力资源"],
      "description": "岗位表，记录公司职位"
    },
    {
      "name": "hr_employees",
      "module": "HR",
      "tags": ["员工", "人力资源", "考勤", "工资", "人员"],
      "description": "员工主表，记录员工基本信息、部门、岗位等"
    },
    {
      "name": "hr_attendance",
      "module": "HR",
      "tags": ["考勤", "打卡", "出勤", "人力资源"],
      "description": "员工考勤记录表"
    },
    {
      "name": "hr_salary",
      "module": "HR",
      "tags": ["工资", "薪酬", "人力资源", "发放"],
      "description": "员工工资表"
    },
    {
      "name": "crm_customers",
      "module": "CRM",
      "tags": ["客户", "客户管理", "信用", "CRM"],
      "description": "客户表，记录客户信息、信用额度等"
    },
    {
      "name": "crm_contacts",
      "module": "CRM",
      "tags": ["联系人", "客户", "联系方式"],
      "description": "客户联系人表"
    },
    {
      "name": "crm_customer_addresses",
      "module": "CRM",
      "tags": ["客户地址", "收货地址"],
      "description": "客户地址表"
    },
    {
      "name": "scm_suppliers",
      "module": "SCM",
      "tags": ["供应商", "供应链", "采购"],
      "description": "供应商表"
    },
    {
      "name": "scm_supplier_contacts",
      "module": "SCM",
      "tags": ["供应商联系人", "供应链"],
      "description": "供应商联系人表"
    },
    {
      "name": "inv_warehouses",
      "module": "INV",
      "tags": ["仓库", "库存", "仓储"],
      "description": "仓库表"
    },
    {
      "name": "inv_locations",
      "module": "INV",
      "tags": ["库位", "货架", "库存"],
      "description": "库位表"
    },
    {
      "name": "inv_product_categories",
      "module": "INV",
      "tags": ["产品分类", "分类", "库存"],
      "description": "产品分类表"
    },
    {
      "name": "inv_products",
      "module": "INV",
      "tags": ["产品", "商品", "库存", "物料"],
      "description": "产品表"
    },
    {
      "name": "inv_inventory",
      "module": "INV",
      "tags": ["库存", "库存量", "仓储"],
      "description": "库存表"
    },
    {
      "name": "inv_inventory_transactions",
      "module": "INV",
      "tags": ["库存事务", "出入库", "流水"],
      "description": "库存事务表"
    },
    {
      "name": "pur_purchase_orders",
      "module": "PUR",
      "tags": ["采购订单", "采购", "供应商"],
      "description": "采购订单表"
    },
    {
      "name": "pur_purchase_order_items",
      "module": "PUR",
      "tags": ["采购明细", "采购订单明细"],
      "description": "采购订单明细表"
    },
    {
      "name": "pur_goods_receipts",
      "module": "PUR",
      "tags": ["到货单", "收货", "采购入库"],
      "description": "到货单表"
    },
    {
      "name": "pur_goods_receipt_items",
      "module": "PUR",
      "tags": ["到货明细", "收货明细"],
      "description": "到货单明细表"
    },
    {
      "name": "sal_orders",
      "module": "SAL",
      "tags": ["销售订单", "订单", "销售", "销售额", "客户订单"],
      "description": "销售订单主表"
    },
    {
      "name": "sal_order_items",
      "module": "SAL",
      "tags": ["订单明细", "销售明细", "订单商品"],
      "description": "销售订单明细表"
    },
    {
      "name": "sal_deliveries",
      "module": "SAL",
      "tags": ["发货单", "发货", "物流"],
      "description": "发货单表"
    },
    {
      "name": "sal_delivery_items",
      "module": "SAL",
      "tags": ["发货明细", "发货商品"],
      "description": "发货单明细表"
    },
    {
      "name": "fin_accounts",
      "module": "FIN",
      "tags": ["财务科目", "会计科目", "财务"],
      "description": "财务科目表"
    },
    {
      "name": "fin_vouchers",
      "module": "FIN",
      "tags": ["凭证", "会计凭证", "财务"],
      "description": "会计凭证表"
    },
    {
      "name": "fin_voucher_details",
      "module": "FIN",
      "tags": ["凭证明细", "分录", "财务"],
      "description": "凭证明细表"
    },
    {
      "name": "fin_journal_entries",
      "module": "FIN",
      "tags": ["日记账", "记账", "财务"],
      "description": "日记账表"
    },
    {
      "name": "pro_projects",
      "module": "PRO",
      "tags": ["项目", "项目管理", "工程"],
      "description": "项目表"
    },
    {
      "name": "pro_project_tasks",
      "module": "PRO",
      "tags": ["项目任务", "任务", "项目"],
      "description": "项目任务表"
    },
    {
      "name": "pro_milestones",
      "module": "PRO",
      "tags": ["里程碑", "项目里程碑"],
      "description": "项目里程碑表"
    },
    {
      "name": "mrp_production_orders",
      "module": "MRP",
      "tags": ["生产订单", "生产", "制造"],
      "description": "生产订单表"
    },
    {
      "name": "mrp_bom",
      "module": "MRP",
      "tags": ["物料清单", "BOM", "生产"],
      "description": "物料清单表"
    },
    {
      "name": "mrp_work_orders",
      "module": "MRP",
      "tags": ["工序", "工作令", "生产"],
      "description": "生产工序表"
    },
    {
      "name": "sys_users",
      "module": "SYS",
      "tags": ["用户", "系统用户", "登录"],
      "description": "系统用户表"
    },
    {
      "name": "sys_roles",
      "module": "SYS",
      "tags": ["角色", "权限角色"],
      "description": "系统角色表"
    },
    {
      "name": "sys_user_roles",
      "module": "SYS",
      "tags": ["用户角色", "权限"],
      "description": "用户角色关联表"
    },
    {
      "name": "sys_permissions",
      "module": "SYS",
      "tags": ["权限", "系统权限"],
      "description": "系统权限表"
    },
    {
      "name": "sys_role_permissions",
      "module": "SYS",
      "tags": ["角色权限", "权限关联"],
      "description": "角色权限关联表"
    },
    {
      "name": "sys_audit_log",
      "module": "SYS",
      "tags": ["审计日志", "操作日志", "日志"],
      "description": "系统审计日志表"
    },
    {
      "name": "wms_employee_schedules",
      "module": "WMS",
      "tags": ["排班", "员工排班", "考勤排班"],
      "description": "员工排班表"
    }
  ]
}
```

- [ ] **Step 2: 提交**

```bash
git add configs/erp_schema.json
git commit -m "feat: 添加 ERP Schema 配置

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 创建 schema_loader.py

**Files:**
- Create: `backend/src/db/schema_loader.py`
- Modify: `backend/src/db/__init__.py` (添加导出)

- [ ] **Step 1: 创建 schema_loader.py**

```python
"""
Schema Loader
读取 erp_schema.json 配置，结合 schema_introspector 动态获取字段详情
"""
import json
import os
from typing import List, Dict, Optional
from .schema_introspector import SchemaIntrospector


class SchemaLoader:
    """Schema 加载器"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # 默认路径
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(backend_dir, '..', 'configs', 'erp_schema.json')
            config_path = os.path.normpath(config_path)

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.tables_config = {t['name']: t for t in self.config.get('tables', [])}

    def get_table_summary(self) -> str:
        """获取所有表的概要（用于 Layer 1 表选择）"""
        lines = []
        for table in self.config.get('tables', []):
            name = table['name']
            module = table.get('module', '')
            tags = ', '.join(table.get('tags', []))
            desc = table.get('description', '')
            lines.append(f"- **{name}** [{module}] {tags}: {desc}")
        return '\n'.join(lines)

    def get_table_details(self, table_names: List[str], introspector: SchemaIntrospector = None) -> str:
        """获取指定表的详细字段（用于 Layer 2 SQL 生成）"""
        lines = []
        for table_name in table_names:
            if table_name not in self.tables_config:
                continue

            config = self.tables_config[table_name]
            lines.append(f"\n### 表: {table_name}")
            lines.append(f"说明: {config.get('description', '')}")
            lines.append("")

            # 获取字段详情
            if introspector:
                try:
                    tables = introspector.get_all_tables()
                    for t in tables:
                        if t.name == table_name:
                            lines.append("| 列名 | 类型 | 可空 | 说明 |")
                            lines.append("|------|------|------|------|")
                            for col in t.columns:
                                nullable = "是" if col.is_nullable else "否"
                                pk = " (PK)" if col.is_primary_key else ""
                                fk = f" (FK → {col.foreign_table}.{col.foreign_column})" if col.is_foreign_key else ""
                                comment = col.comment or ""
                                lines.append(f"| {col.name} | {col.data_type}{pk}{fk} | {nullable} | {comment} |")
                            break
                except Exception:
                    pass

            if not introspector or f"### 表: {table_name}" not in '\n'.join(lines):
                # 如果没有 introspector，使用配置文件中的 tags 作为说明
                lines.append(f"已知字段提示: {', '.join(config.get('tags', []))}")

        return '\n'.join(lines)

    def get_all_tables(self) -> List[str]:
        """获取所有表名列表"""
        return [t['name'] for t in self.config.get('tables', [])]

    def get_table_config(self, table_name: str) -> Optional[Dict]:
        """获取指定表的配置"""
        return self.tables_config.get(table_name)

    def get_modules(self) -> List[str]:
        """获取所有模块"""
        return self.config.get('modules', [])
```

- [ ] **Step 2: 更新 __init__.py**

```python
# backend/src/db/__init__.py
from .manager import ConnectionManager, get_connection_manager
from .schema_loader import SchemaLoader
from .schema_introspector import SchemaIntrospector
from .sql_validator import SQLValidator, ValidationResult

__all__ = [
    'ConnectionManager',
    'get_connection_manager',
    'SchemaLoader',
    'SchemaIntrospector',
    'SQLValidator',
    'ValidationResult'
]
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/db/schema_loader.py backend/src/db/__init__.py
git commit -m "feat: 添加 SchemaLoader

- 读取 erp_schema.json 配置
- 提供表概要和详情加载

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 创建 sql_validator.py

**Files:**
- Create: `backend/src/db/sql_validator.py`

- [ ] **Step 1: 创建 sql_validator.py**

```python
"""
SQL Validator
SQL 验证层：语法验证、表名验证、危险操作检查
"""
import re
from typing import List, Set, Tuple, Optional
from dataclasses import dataclass
try:
    import sqlparse
    HAS_SQLPARSE = True
except ImportError:
    HAS_SQLPARSE = False


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    error: Optional[str] = None
    extracted_tables: List[str] = []

    @classmethod
    def success(cls, tables: List[str] = None) -> 'ValidationResult':
        return cls(valid=True, extracted_tables=tables or [])

    @classmethod
    def failure(cls, error: str) -> 'ValidationResult':
        return cls(valid=False, error=error)


class SQLValidator:
    """SQL 验证器"""

    # 危险操作关键词
    DANGEROUS_PATTERNS = [
        'DROP', 'TRUNCATE', 'ALTER', 'DELETE', 'INSERT', 'UPDATE',
        'CREATE', 'GRANT', 'REVOKE', 'EXECUTE', 'COPY', 'PG_READ_FILE',
        'PG_WRITE_FILE', 'LO_IMPORT', 'LO_EXPORT'
    ]

    def __init__(self):
        pass

    def validate(self, sql: str, valid_tables: List[str]) -> ValidationResult:
        """
        验证 SQL

        Args:
            sql: SQL 语句
            valid_tables: 有效的表名列表

        Returns:
            ValidationResult
        """
        if not sql or not sql.strip():
            return ValidationResult.failure("SQL 不能为空")

        # 1. 语法验证
        syntax_result = self.validate_syntax(sql)
        if not syntax_result[0]:
            return ValidationResult.failure(f"SQL 语法错误: {syntax_result[1]}")

        # 2. 提取并验证表名
        extracted_tables = self.extract_tables(sql)
        for table in extracted_tables:
            if table not in valid_tables:
                return ValidationResult.failure(f"表 '{table}' 不存在或不在允许范围内")

        # 3. 危险操作检查
        danger_result = self.check_dangerous_operations(sql)
        if not danger_result[0]:
            return ValidationResult.failure(f"禁止的操作: {danger_result[1]}")

        return ValidationResult.success(extracted_tables)

    def validate_syntax(self, sql: str) -> Tuple[bool, str]:
        """验证 SQL 语法"""
        if HAS_SQLPARSE:
            try:
                parsed = sqlparse.parse(sql)
                if not parsed:
                    return False, "无法解析 SQL"
                # 检查是否只有 SELECT
                for stmt in parsed:
                    if stmt.get_type() == 'UNKNOWN':
                        # 可能是无效语法
                        if not str(stmt).strip().upper().startswith('SELECT'):
                            return False, "只允许 SELECT 查询"
                return True, ""
            except Exception as e:
                return False, str(e)
        else:
            # 没有 sqlparse，简单检查
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith('SELECT'):
                return False, "只允许 SELECT 查询"
            return True, ""

    def extract_tables(self, sql: str) -> List[str]:
        """从 SQL 中提取表名"""
        tables = set()

        # 简单正则提取 FROM 和 JOIN 后的表名
        patterns = [
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        ]

        sql_upper = sql.upper()
        for pattern in patterns:
            matches = re.findall(pattern, sql_upper, re.IGNORECASE)
            tables.update([m.lower() for m in matches])

        return list(tables)

    def check_dangerous_operations(self, sql: str) -> Tuple[bool, str]:
        """检查危险操作"""
        sql_upper = sql.upper()

        # 检查完整的单词边界
        for pattern in self.DANGEROUS_PATTERNS:
            # 使用单词边界检查
            if re.search(r'\b' + pattern + r'\b', sql_upper):
                return False, pattern

        return True, ""

    def sanitize_sql(self, sql: str) -> str:
        """清理 SQL"""
        # 移除多余空白
        sql = ' '.join(sql.split())
        return sql
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/db/sql_validator.py
git commit -m "feat: 添加 SQLValidator 验证层

- 语法验证（使用 sqlparse）
- 表名提取和验证
- 危险操作检查

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 创建 agents/table_selector.py (Layer 1)

**Files:**
- Create: `backend/src/agents/table_selector.py`
- Create: `backend/src/agents/__init__.py`

- [ ] **Step 1: 创建 table_selector.py**

```python
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
- 输入: "统计销售额" 输出: sal_orders, sal_order_items
"""

    def __init__(self, schema_loader: SchemaLoader, llm_client: LLMClient):
        self.schema_loader = schema_loader
        self.llm_client = llm_client

    def select_tables(self, user_query: str, retry: int = 2) -> List[str]:
        """
        选择相关表

        Args:
            user_query: 用户查询
            retry: 重试次数

        Returns:
            表名列表
        """
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
                    # 最后一次尝试失败，返回空列表
                    return []

        return []

    def _parse_response(self, response: str) -> List[str]:
        """解析 LLM 返回的表名列表"""
        # 清理返回内容
        response = response.strip()

        # 提取表名（逗号分隔）
        parts = re.split(r'[,，、\n]', response)
        tables = []
        all_valid_tables = set(self.schema_loader.get_all_tables())

        for part in parts:
            part = part.strip()
            # 清理可能的序号或前缀
            part = re.sub(r'^\d+[\.、]\s*', '', part)
            part = part.strip()

            if part and part in all_valid_tables:
                tables.append(part)

        return tables
```

- [ ] **Step 2: 创建 agents/__init__.py**

```python
# backend/src/agents/__init__.py
from .table_selector import TableSelector
from .sql_generator import SQLGenerator
from .result_summarizer import ResultSummarizer

__all__ = ['TableSelector', 'SQLGenerator', 'ResultSummarizer']
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/agents/table_selector.py backend/src/agents/__init__.py
git commit -m "feat: 添加 TableSelector (Layer 1)

- 根据用户问题判断需要哪些表
- 使用 LLM 进行表选择
- 支持重试机制

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: 创建 agents/sql_generator.py (Layer 2)

**Files:**
- Create: `backend/src/agents/sql_generator.py`

- [ ] **Step 1: 创建 sql_generator.py**

```python
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
        """
        生成 SQL

        Args:
            user_query: 用户查询
            table_names: 相关表名列表
            retry: 重试次数

        Returns:
            (sql, explanation) 元组
        """
        # 获取表详情
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

        # 提取 SQL
        sql_match = re.search(r'SQL:\s*(.+?)(?=解释:|$)', response, re.DOTALL | re.IGNORECASE)
        sql = sql_match.group(1).strip() if sql_match else ""

        # 提取解释
        exp_match = re.search(r'解释:\s*(.+?)(?=$)', response, re.DOTALL | re.IGNORECASE)
        explanation = exp_match.group(1).strip() if exp_match else ""

        # 清理 SQL
        sql = sql.strip()
        if sql and not sql.endswith(';'):
            sql = sql + ';'

        return sql, explanation
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/agents/sql_generator.py
git commit -m "feat: 添加 SQLGenerator (Layer 2)

- 根据用户问题和表结构生成 SQL
- 解析 LLM 返回的 SQL 和解释
- PostgreSQL 语法正确性

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: 创建 agents/result_summarizer.py (Layer 3)

**Files:**
- Create: `backend/src/agents/result_summarizer.py`

- [ ] **Step 1: 创建 result_summarizer.py**

```python
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
        """
        生成结果摘要

        Args:
            columns: 列名列表
            rows: 数据行列表
            retry: 重试次数

        Returns:
            摘要文本
        """
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
```

- [ ] **Step 2: 提交**

```bash
git add backend/src/agents/result_summarizer.py
git commit -m "feat: 添加 ResultSummarizer (Layer 3)

- 对查询结果进行 AI 摘要
- 限制数据量避免 token 浪费

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: 创建 api/text2sql.py

**Files:**
- Create: `backend/src/api/text2sql.py`
- Modify: `backend/src/main.py` (注册路由)

- [ ] **Step 1: 创建 text2sql.py**

```python
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


# 请求模型
class Text2SQLRequest(BaseModel):
    connection_id: str
    query: str


class Text2SQLExecuteRequest(BaseModel):
    connection_id: str
    sql: str


# 响应模型
class Text2SQLResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端"""
    from ..core.config import get_config
    config = get_config()
    llm_config = config.get('llm', {})
    return LLMClient(llm_config)


def get_schema_loader() -> SchemaLoader:
    """获取 Schema 加载器"""
    return SchemaLoader()


def get_introspector(connection_id: str) -> SchemaIntrospector:
    """获取 Schema Introspector"""
    from ..db.manager import get_connection_manager
    from ..core.config import get_config

    config = get_config()
    manager = get_connection_manager(config.get('database', {}))

    # 从 connection_id 获取连接配置
    # 这里简化处理，实际应从 manager 获取连接详情
    db_config = config.get('database', {})

    return SchemaIntrospector(
        host=db_config.get('host', 'localhost'),
        port=db_config.get('port', 5432),
        database='erp_simulation',  # 使用 erp_simulation 数据库
        username=db_config.get('username', 'cjwdsg'),
        password=db_config.get('password', '')
    )


@router.post("/text2sql")
async def generate_sql(req: Text2SQLRequest) -> Text2SQLResponse:
    """
    Text2SQL：生成 SQL
    """
    try:
        # 初始化组件
        schema_loader = get_schema_loader()
        introspector = get_introspector(req.connection_id)
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
    """
    Text2SQL：执行 SQL
    """
    try:
        # 验证 SQL
        schema_loader = get_schema_loader()
        validator = SQLValidator()
        valid_tables = schema_loader.get_all_tables()
        validation = validator.validate(req.sql, valid_tables)

        if not validation.valid:
            return Text2SQLResponse(
                success=False,
                error=validation.error
            )

        # 执行查询
        from sqlalchemy import create_engine, text
        from ..core.config import get_config

        config = get_config()
        db_config = config.get('database', {})

        engine = create_engine(
            f"postgresql://{db_config.get('username', 'cjwdsg')}:{db_config.get('password', '')}"
            f"@{db_config.get('host', 'localhost')}:{db_config.get('port', 5432)}/erp_simulation"
        )

        start_time = time.time()
        with engine.connect() as conn:
            result = conn.execute(text(req.sql))
            rows = result.fetchmany(1000)  # 限制返回行数
            columns = list(result.keys())
            execution_time_ms = int((time.time() - start_time) * 1000)

        # 转换为字典
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
```

- [ ] **Step 2: 更新 main.py 注册路由**

```python
# backend/src/main.py 添加
from .api import chat, db, admin, text2sql

# 注册路由
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(db.router, prefix="/api/db", tags=["database"])
app.include_router(text2sql.router, prefix="/api/db", tags=["text2sql"])  # 添加这行
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
```

- [ ] **Step 3: 提交**

```bash
git add backend/src/api/text2sql.py backend/src/main.py
git commit -m "feat: 添加 Text2SQL API

- POST /api/db/text2sql - 生成 SQL
- POST /api/db/text2sql/execute - 执行 SQL
- 三层 LLM 架构集成

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: 修改前端 Query 页面

**Files:**
- Modify: `frontend/src/pages/Query/index.tsx`

- [ ] **Step 1: 修改 Query/index.tsx**

将原有的 Query 页面改造为支持 AI 辅助：

```tsx
import { useState, useEffect } from 'react'
import { Button, Select, Table, Tabs, Space, message, Spin, Alert } from 'antd'
import {
  PlayCircleOutlined,
  ThunderboltOutlined,
  RobotOutlined,
  SendOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Option } = Select

interface QueryResult {
  key: string
  [key: string]: any
}

interface Text2SQLResponse {
  sql: string
  explanation: string
  affected_tables: string[]
}

export default function Query() {
  const [sql, setSql] = useState('')
  const [loading, setLoading] = useState(false)
  const [connectionId, setConnectionId] = useState<string>('')
  const [connections, setConnections] = useState<any[]>([])

  // AI 辅助状态
  const [aiMode, setAiMode] = useState(false)
  const [userQuery, setUserQuery] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [generatedSql, setGeneratedSql] = useState<Text2SQLResponse | null>(null)
  const [executeLoading, setExecuteLoading] = useState(false)

  // 查询结果状态
  const [queryResult, setQueryResult] = useState<{
    columns: string[]
    rows: any[]
    execution_time_ms: number
    summary: string
  } | null>(null)
  const [executionTime, setExecutionTime] = useState<number>(0)

  useEffect(() => {
    fetchConnections()
  }, [])

  const fetchConnections = async () => {
    try {
      const res = await fetch('/api/db/connections')
      const data = await res.json()
      setConnections(data.connections || [])
      // 默认选择第一个连接
      if (data.connections?.length > 0) {
        setConnectionId(data.connections[0].id)
      }
    } catch (e) {
      message.error('获取连接列表失败')
    }
  }

  const handleAiGenerate = async () => {
    if (!userQuery.trim()) {
      message.warning('请输入查询需求')
      return
    }
    if (!connectionId) {
      message.warning('请先选择数据库连接')
      return
    }

    setAiLoading(true)
    setGeneratedSql(null)
    setQueryResult(null)

    try {
      const res = await fetch('/api/db/text2sql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection_id: connectionId, query: userQuery })
      })
      const data = await res.json()

      if (data.success) {
        setGeneratedSql(data.data)
        setSql(data.data.sql)
        message.success('SQL 生成成功，请确认后执行')
      } else {
        message.error(data.error || 'SQL 生成失败')
      }
    } catch (e) {
      message.error('生成失败，请重试')
    } finally {
      setAiLoading(false)
    }
  }

  const handleExecute = async () => {
    const sqlToExecute = aiMode ? generatedSql?.sql : sql
    if (!sqlToExecute?.trim()) {
      message.warning('请输入 SQL 语句')
      return
    }
    if (!connectionId) {
      message.warning('请先选择数据库连接')
      return
    }

    setExecuteLoading(true)
    setQueryResult(null)

    try {
      const startTime = Date.now()
      const res = await fetch('/api/db/text2sql/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection_id: connectionId, sql: sqlToExecute })
      })
      const data = await res.json()
      const elapsed = Date.now() - startTime

      if (data.success) {
        setQueryResult({
          columns: data.data.columns,
          rows: data.data.rows,
          execution_time_ms: data.data.execution_time_ms || elapsed,
          summary: data.data.summary || ''
        })
        setExecutionTime(data.data.execution_time_ms || elapsed)
        message.success(`查询成功，返回 ${data.data.row_count || 0} 行`)
      } else {
        message.error(data.error || '查询失败')
      }
    } catch (e) {
      message.error('查询执行失败')
    } finally {
      setExecuteLoading(false)
    }
  }

  const columns: ColumnsType<QueryResult> = queryResult
    ? queryResult.columns.map((col) => ({
        title: col,
        dataIndex: col,
        key: col,
        ellipsis: true,
        width: 150
      }))
    : []

  const tabItems = [
    {
      key: 'results',
      label: '结果',
      children: (
        queryResult && queryResult.rows.length > 0 ? (
          <Table
            columns={columns}
            dataSource={queryResult.rows.map((row, index) => ({ ...row, key: String(index) }))}
            rowKey="key"
            pagination={{ pageSize: 10, showSizeChanger: true }}
            size="small"
            scroll={{ x: 800 }}
          />
        ) : (
          <div className="p-8 text-center text-gray-500">
            {sql.trim() ? '点击"执行"按钮运行查询' : '请输入 SQL 语句或使用 AI 生成'}
          </div>
        )
      )
    },
    {
      key: 'summary',
      label: '数据摘要',
      children: (
        queryResult?.summary ? (
          <div className="p-4">
            <Alert message={queryResult.summary} type="info" showIcon />
          </div>
        ) : (
          <div className="p-4 text-gray-500">执行查询后查看数据摘要</div>
        )
      )
    }
  ]

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold m-0">SQL 查询</h1>
        <Space>
          <Button
            icon={<RobotOutlined />}
            type={aiMode ? 'primary' : 'default'}
            onClick={() => setAiMode(!aiMode)}
            className={aiMode ? 'bg-blue-500' : ''}
          >
            AI 辅助
          </Button>
          <Select
            placeholder="选择连接"
            value={connectionId || undefined}
            onChange={setConnectionId}
            style={{ width: 200 }}
            showSearch
            filterOption={(input, option) =>
              (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
            }
          >
            {connections.map((conn) => (
              <Option key={conn.id} value={conn.id}>{conn.name}</Option>
            ))}
          </Select>
        </Space>
      </div>

      {/* AI 辅助输入区域 */}
      {aiMode && (
        <div className="mb-4 bg-blue-50 rounded-lg p-4">
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              className="flex-1 px-3 py-2 border rounded"
              placeholder="用自然语言描述你的查询需求，如：查过去一年销售额最高的10个客户"
              value={userQuery}
              onChange={(e) => setUserQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAiGenerate()}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleAiGenerate}
              loading={aiLoading}
              className="bg-blue-500"
            >
              生成 SQL
            </Button>
          </div>

          {/* 生成结果显示 */}
          {aiLoading && (
            <div className="text-center py-4">
              <Spin tip="正在分析需求并生成 SQL..." />
            </div>
          )}

          {generatedSql && !aiLoading && (
            <div className="bg-white rounded p-3">
              <div className="text-sm text-gray-600 mb-2">
                <RobotOutlined className="mr-1" />
                判断使用的表：
                <span className="font-mono ml-1">{generatedSql.affected_tables?.join(', ')}</span>
              </div>
              <div className="text-sm text-gray-600 mb-2">
                解释：{generatedSql.explanation}
              </div>
              <div className="bg-gray-100 rounded p-2 font-mono text-sm">
                {generatedSql.sql}
              </div>
            </div>
          )}
        </div>
      )}

      {/* SQL 输入框 */}
      <div className="mb-4">
        <div className="bg-gray-800 rounded-lg p-4 text-white font-mono text-sm">
          <textarea
            className="w-full bg-transparent text-white font-mono text-sm outline-none resize-none"
            rows={aiMode ? 3 : 6}
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            placeholder="输入 SQL 语句..."
          />
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2 mb-4">
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleExecute}
          loading={executeLoading}
          className="bg-blue-500"
        >
          执行
        </Button>
        {aiMode && generatedSql && (
          <Button
            icon={<RobotOutlined />}
            onClick={() => {
              setSql('')
              setGeneratedSql(null)
              setUserQuery('')
            }}
          >
            重新生成
          </Button>
        )}
        {executionTime > 0 && (
          <span className="ml-4 text-gray-500 self-center">
            执行时间: {executionTime}ms
          </span>
        )}
      </div>

      {/* 结果区域 */}
      <div className="flex-1 bg-white border rounded-lg overflow-hidden">
        <Tabs items={tabItems} className="p-4" />
      </div>
    </div>
  )
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/Query/index.tsx
git commit -m "feat: 添加 AI 辅助 SQL 查询界面

- AI 模式切换
- 自然语言输入
- SQL 生成和确认执行
- 数据摘要展示

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 9: 安装依赖并测试

**Files:**
- Modify: `backend/requirements.txt` (添加 sqlparse)

- [ ] **Step 1: 添加依赖**

```bash
echo "sqlparse>=0.4.0" >> backend/requirements.txt
```

- [ ] **Step 2: 安装依赖**

```bash
cd backend
pip install sqlparse
```

- [ ] **Step 3: 重启后端服务**

```bash
# 停止现有服务
lsof -i :8000 -t | xargs kill -9

# 重新启动
cd /Users/cjwdsg/smart-assistant/backend
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 &
```

- [ ] **Step 4: 测试 API**

```bash
# 测试 text2sql 生成
curl -X POST http://localhost:8000/api/db/text2sql \
  -H "Content-Type: application/json" \
  -d '{"connection_id": "test", "query": "查所有员工"}'
```

- [ ] **Step 5: 提交**

```bash
git add backend/requirements.txt
git commit -m "chore: 添加 sqlparse 依赖

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 10: 完整测试

- [ ] **Step 1: 测试场景**

测试以下场景：
1. "查所有员工"
2. "过去一年销售额最高的10个客户"
3. "统计每个部门的平均工资"
4. "找出库存低于安全存量的产品"

- [ ] **Step 2: 修复问题**

根据测试结果修复问题

- [ ] **Step 3: 最终提交**

```bash
git add -A
git commit -m "feat: 完成 Text2SQL 智能查询系统

- 三层 LLM 架构
- 自然语言转 SQL
- AI 数据摘要
- 用户确认执行机制

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 执行选项

**1. Subagent-Driven (推荐)** - 任务分派给子 agent 执行
**2. Inline Execution** - 在当前会话执行，批量处理带检查点

**选择哪个方式？**
