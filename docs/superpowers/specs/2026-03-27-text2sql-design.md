# Text2SQL 智能查询系统设计

## 1. 概述

在 SQL 查询页面嵌入 AI 能力，通过自然语言描述自动生成 SQL 查询语句，解决用户不知道有哪些表、表字段含义等问题。

### 核心目标
- 用户可以用自然语言描述查询需求
- 系统自动判断需要哪些表、生成对应 SQL
- 用户确认 SQL 后再执行，保证安全性
- 对查询结果提供 AI 摘要解读

## 2. 架构设计

### 2.1 三层 LLM 架构

```
用户输入: "查过去一年销售额最高的10个客户"
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 1: 表选择 (Table Selector)           │
│  输入: 用户问题 + 表概要 JSON                 │
│  输出: 相关表列表                           │
│  Token 消耗: ~500 tokens                   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 2: SQL 生成 (SQL Generator)          │
│  输入: 用户问题 + 相关表字段详情               │
│  输出: SQL 语句 + SQL 解释                  │
│  Token 消耗: ~2000 tokens                  │
└─────────────────────────────────────────────┘
                    ↓
            ┌───────────────────┐
            │  用户确认执行      │
            └───────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 3: 结果摘要 (Result Summarizer)       │
│  输入: 查询结果 + 列名                       │
│  输出: 数据含义解读                          │
└─────────────────────────────────────────────┘
```

### 2.2 数据流

```
configs/erp_schema.json     ←── 表用途/标签配置
        ↓
schema_loader.py            ←── 读取配置 + 补充 DB 字段
        ↓
table_selector.py           ←── Layer 1 LLM
        ↓
sql_generator.py            ←── Layer 2 LLM
        ↓
execute_query()            ←── 用户确认后执行
        ↓
result_summarizer.py       ←── Layer 3 LLM
```

## 3. 组件设计

### 3.1 erp_schema.json

**位置**: `configs/erp_schema.json`

**用途**: 定义每个表的模块归属、标签、描述，供 Layer 1 判断用户意图

```json
{
  "version": "1.0",
  "description": "ERP 仿真数据库 Schema 配置",
  "modules": ["HR", "CRM", "SCM", "INV", "PUR", "SAL", "FIN", "PRO", "MRP", "SYS", "WMS"],
  "tables": [
    {
      "name": "hr_employees",
      "module": "HR",
      "tags": ["员工", "人力资源", "考勤", "工资"],
      "description": "员工主表，记录员工基本信息、部门、岗位等"
    },
    {
      "name": "hr_departments",
      "module": "HR",
      "tags": ["部门", "组织架构"],
      "description": "部门表，记录公司组织结构"
    },
    {
      "name": "crm_customers",
      "module": "CRM",
      "tags": ["客户", "客户管理", "信用"],
      "description": "客户表，记录客户信息、信用额度等"
    },
    {
      "name": "sal_orders",
      "module": "SAL",
      "tags": ["销售", "订单", "销售额"],
      "description": "销售订单主表"
    },
    {
      "name": "sal_order_items",
      "module": "SAL",
      "tags": ["订单明细", "销售明细"],
      "description": "销售订单明细表"
    }
  ]
}
```

### 3.2 schema_loader.py

**位置**: `backend/src/db/schema_loader.py`

**职责**:
1. 读取 `erp_schema.json` 获取表配置
2. 通过 `schema_introspector.py` 动态获取表的字段信息
3. 组装完整上下文供 LLM 使用

**核心方法**:
```python
class SchemaLoader:
    def get_table_summary(self) -> str
        """获取所有表的概要（用于 Layer 1）"""

    def get_table_details(self, table_names: List[str]) -> str
        """获取指定表的详细字段（用于 Layer 2）"""

    def get_all_tables(self) -> List[str]
        """获取所有表名列表"""
```

### 3.3 table_selector.py (Layer 1)

**位置**: `backend/src/agents/table_selector.py`

**输入 Prompt**:
```
你是一个 ERP 数据库专家。用户想要执行以下查询：
"{用户问题}"

以下是我们 ERP 系统中的表及其描述：
{表概要列表}

请判断用户可能需要查询哪些表，返回表名列表。
只返回表名，用逗号分隔，不要其他内容。

示例输出: hr_employees, sal_orders, crm_customers
```

**输出**: `hr_employees, sal_orders, crm_customers`

### 3.4 sql_generator.py (Layer 2)

**位置**: `backend/src/agents/sql_generator.py`

**输入 Prompt**:
```
你是一个 ERP 数据库专家，擅长根据用户需求生成 PostgreSQL SQL。

用户想要查询：
"{用户问题}"

请根据以下表结构生成 SQL：

{相关表字段详情}

要求：
1. 只生成 SELECT 查询，不要 INSERT/UPDATE/DELETE
2. 使用正确的 PostgreSQL 语法
3. 表名和列名使用实际名称，不要臆造
4. 如果需要 JOIN，确保外键关系正确

请按以下格式返回：
SQL: <生成的 SQL 语句>
解释: <SQL 的简要说明>
```

**输出**:
```
SQL: SELECT c.name, SUM(oi.amount) as total_sales
     FROM sal_orders o
     JOIN crm_customers c ON o.customer_id = c.id
     JOIN sal_order_items oi ON o.id = oi.order_id
     WHERE o.order_date >= CURRENT_DATE - INTERVAL '1 year'
     GROUP BY c.id, c.name
     ORDER BY total_sales DESC
     LIMIT 10
解释: 这个 SQL 首先在 sal_orders 表...
```

### 3.5 result_summarizer.py (Layer 3)

**位置**: `backend/src/agents/result_summarizer.py`

**输入 Prompt**:
```
你是一个数据分析专家。用户的查询返回了以下结果：

查询结果（共 {row_count} 行）：
列名：{columns}
数据：
{rows}

请用 2-3 句话总结这批数据的主要发现和含义。
```

**输出**: "过去一年销售额最高的 10 个客户中，深圳科技有限公司以 128 万元总额位居第一..."

## 4. API 设计

### 4.1 Text2SQL 生成

```
POST /api/db/text2sql
```

**Request**:
```json
{
  "connection_id": "xxx-xxx-xxx",
  "query": "查过去一年销售额最高的10个客户"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "sql": "SELECT c.name, SUM(oi.amount)... ",
    "explanation": "这个 SQL 首先在 sal_orders...",
    "affected_tables": ["crm_customers", "sal_orders", "sal_order_items"],
    "estimated_rows": 10
  }
}
```

### 4.2 SQL 执行

```
POST /api/db/text2sql/execute
```

**Request**:
```json
{
  "connection_id": "xxx-xxx-xxx",
  "sql": "SELECT c.name, SUM(oi.amount)..."
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "columns": ["name", "total_sales"],
    "rows": [
      {"name": "深圳科技有限公司", "total_sales": 1280000},
      ...
    ],
    "row_count": 10,
    "execution_time_ms": 156,
    "summary": "过去一年销售额最高的10个客户中，深圳科技有限公司以128万元总额位居第一..."
  }
}
```

## 5. 前端设计

### 5.1 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  SQL 查询                                           [AI 辅助] │
├─────────────────────────────────────────────────────────────┤
│  [连接选择器]                                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 请输入您想查询的内容...                    [AI 生成]  │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ AI 辅助 ─────────────────────────────────────────────┐ │
│  │ 📋 判断使用的表: sal_orders, crm_customers           │ │
│  │                                                     │ │
│  │ 已生成的 SQL:                                        │ │
│  │ SELECT c.name, SUM(oi.amount)...                    │ │
│  │                                                     │ │
│  │ 解释: 这个 SQL 首先...                                │ │
│  │                                                     │ │
│  │              [执行 SQL]  [修改需求]                  │ │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  执行时间: 156ms                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 结果表格                                              │   │
│  │ name            | total_sales                        │   │
│  │ 深圳科技有限公司 | 1,280,000                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ 数据摘要 ─────────────────────────────────────────────┐ │
│  │ 过去一年销售额最高的10个客户中，深圳科技有限公司以        │ │
│  │ 128万元总额位居第一...                                 │ │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 组件状态

| 状态 | 显示内容 |
|------|----------|
| 初始 | AI 生成按钮 |
| 生成中 | Loading 动画 + "正在分析需求..." |
| 已生成 | SQL + 解释 + 执行按钮 |
| 执行中 | Loading + 执行进度 |
| 已完成 | 结果表格 + 数据摘要 |
| 错误 | 错误信息 + 重试按钮 |

## 6. LLM 配置

### 6.1 Provider 配置

使用 MiniMax M2.7 模型，通过 OpenAI 兼容格式调用：

```python
llm_config = {
    "provider": "minimax",
    "model": "MiniMax-M2.7",
    "api_key": "xxx",
    "base_url": "https://api.minimaxi.com/v1"
}
```

### 6.2 Layer 调用策略

| Layer | 模型 | Temperature | Token 预算 |
|-------|------|-------------|------------|
| Layer 1 表选择 | MiniMax-M2.7 | 0.1 | ~500 |
| Layer 2 SQL生成 | MiniMax-M2.7 | 0.1 | ~2000 |
| Layer 3 结果摘要 | MiniMax-M2.7 | 0.3 | ~300 |

## 7. 安全性考虑

### 7.1 SQL 执行限制

- **只允许 SELECT** — 生成器 Prompt 明确禁止 INSERT/UPDATE/DELETE
- **超时限制** — 查询最多执行 30 秒
- **行数限制** — 默认返回最多 1000 行
- **高危操作拦截** — 包含 `DROP`、`TRUNCATE`、`ALTER` 等关键词直接拒绝

### 7.2 错误处理

- LLM 生成失败 → 返回友好错误提示
- SQL 语法错误 → 显示错误信息，允许用户修改
- 执行超时 → 中断查询，提示优化建议
- 连接失败 → 提示检查数据库连接

## 8. 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `configs/erp_schema.json` | 新建 | 表结构配置 |
| `backend/src/db/schema_loader.py` | 新建 | Schema 读取器 |
| `backend/src/agents/table_selector.py` | 新建 | Layer 1 表选择 |
| `backend/src/agents/sql_generator.py` | 新建 | Layer 2 SQL 生成 |
| `backend/src/agents/result_summarizer.py` | 新建 | Layer 3 结果摘要 |
| `backend/src/api/text2sql.py` | 新建 | Text2SQL API |
| `frontend/src/pages/Query/index.tsx` | 修改 | AI 辅助查询界面 |

## 9. 依赖

### Python
- psycopg2-binary (已安装)
- openai >= 1.0

### Frontend
- 复用现有 antd, react 依赖
- 无需新增

## 10. 测试计划

### 10.1 单元测试
- schema_loader 读取正确
- table_selector 输出格式正确
- sql_generator 生成有效 SQL

### 10.2 集成测试
- 完整流程: 问题 → SQL → 执行 → 摘要
- 验证生成的 SQL 在数据库执行成功

### 10.3 手工测试场景
1. "查所有员工"
2. "过去一年销售额最高的10个客户"
3. "统计每个部门的平均工资"
4. "找出库存低于安全存量的产品"
