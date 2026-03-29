# Architecture Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 消除全局单例模式、统一数据库连接管理、拆分 God Modules、为最终合并双源码树打下基础。

**Architecture:** 引入 FastAPI 依赖注入（Lifespan + `Depends`）替代全局单例；建立统一的 `DatabaseManager` 封装所有连接；对大模块按职责拆分为独立文件。

**Tech Stack:** FastAPI, SQLAlchemy, psycopg2

---

## 文件变更总览

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/src/core/dependencies.py` | 新建 | FastAPI 依赖注入容器，统一提供 LLMClient、ConnectionManager 等 |
| `backend/src/db/database.py` | 新建 | 统一的数据库连接管理，替代散落的 psycopg2/SQLAlchemy 调用 |
| `backend/src/api/chat.py` | 修改 | 改用 `Depends` 获取 ChatService |
| `backend/src/api/db.py` | 修改 | 改用 `Depends` 获取连接，去除 inline engine 创建 |
| `backend/src/api/text2sql.py` | 修改 | 提取 `generate_sql`、`execute_sql` 为独立函数 |
| `backend/src/api/text2sql/generate.py` | 新建 | NL→SQL 生成逻辑（从 text2sql.py 拆分） |
| `backend/src/api/text2sql/explain.py` | 新建 | SQL 执行 + EXPLAIN（从 text2sql.py 拆分） |
| `backend/src/api/text2sql/templates.py` | 新建 | 模板匹配逻辑（从 text2sql.py 拆分） |
| `backend/src/plugins/builtin/query_executor.py` | 修改 | 通过 PluginContext 获取连接，而非直接调用 `get_monitor_connection()` |
| `backend/src/plugins/builtin/slow_query_analyzer.py` | 修改 | 同上 |
| `backend/src/plugins/base.py` | 修改 | 引入 `PluginContext` 抽象接口 |
| `backend/src/core/service.py` | 修改 | 接收依赖注入的 registry，不再 import 时创建 |
| `backend/src/db/connection.py` | 修改 | 保留 `get_monitor_connection()` 但作为 `DatabaseManager` 的简便封装 |
| `backend/src/db/manager.py` | 修改 | 移除模块级 `_manager` 全局变量 |
| `backend/src/db/template_manager.py` | 修改 | 移除模块级 `_template_manager` 全局变量 |

---

## Task 1: 建立 FastAPI 依赖注入容器

**Files:**
- Create: `backend/src/core/dependencies.py`

- [ ] **Step 1: 创建依赖注入容器**

```python
"""
FastAPI 依赖注入容器
统一提供 LLMClient、ConnectionManager、TemplateManager、PluginRegistry
"""
from functools import lru_cache
from typing import Optional
from .llm import LLMClient
from ..db.manager import ConnectionManager
from ..db.template_manager import TemplateManager
from ..plugins.registry import PluginRegistry


class Container:
    """依赖注入容器"""
    _llm_client: Optional[LLMClient] = None
    _connection_manager: Optional[ConnectionManager] = None
    _template_manager: Optional[TemplateManager] = None
    _registry: Optional[PluginRegistry] = None

    def init(self, config: dict):
        self._llm_client = LLMClient(config.get("llm", {}))
        db_config = config.get("database", {})
        self._connection_manager = ConnectionManager(db_config)
        self._template_manager = TemplateManager()
        self._registry = PluginRegistry()
        # 注册插件
        from ..plugins.builtin import register_all
        register_all(self._registry)

    @property
    def llm_client(self) -> LLMClient:
        if self._llm_client is None:
            raise RuntimeError("Container not initialized")
        return self._llm_client

    @property
    def connection_manager(self) -> ConnectionManager:
        if self._connection_manager is None:
            raise RuntimeError("Container not initialized")
        return self._connection_manager

    @property
    def template_manager(self) -> TemplateManager:
        if self._template_manager is None:
            raise RuntimeError("Container not initialized")
        return self._template_manager

    @property
    def registry(self) -> PluginRegistry:
        if self._registry is None:
            raise RuntimeError("Container not initialized")
        return self._registry


_container = Container()


def get_container() -> Container:
    return _container


@lru_cache
def get_llm_client() -> LLMClient:
    return _container.llm_client


def get_connection_manager() -> ConnectionManager:
    return _container.connection_manager


def get_template_manager() -> TemplateManager:
    return _container.template_manager


def get_registry() -> PluginRegistry:
    return _container.registry
```

- [ ] **Step 2: 修改 main.py，在启动时初始化容器**

```python
# 在 main.py 的 lifespan 中添加:
@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.core.dependencies import get_container
    from src.config import get_config
    container = get_container()
    container.init(get_config())
    yield

app = FastAPI(lifespan=lifespan)
```

- [ ] **Step 3: 验证 FastAPI 启动正常**

Run: `cd backend && python -c "from src.core.dependencies import get_container; print('OK')"`
Expected: 输出 "OK"，无导入错误

- [ ] **Step 4: Commit**

```bash
git add backend/src/core/dependencies.py backend/src/main.py
git commit -m "refactor: 建立 FastAPI 依赖注入容器"
```

---

## Task 2: 统一数据库连接管理

**Files:**
- Create: `backend/src/db/database.py`
- Modify: `backend/src/db/connection.py:9-27`
- Modify: `backend/src/db/manager.py:149-158`
- Modify: `backend/src/api/db.py:45-48`

- [ ] **Step 1: 创建统一的 DatabaseManager**

```python
"""
统一的数据库连接管理
所有数据库连接均通过此类获取，消除 psycopg2/SQLAlchemy 调用碎片化
"""
import psycopg2
from typing import Optional
from contextlib import contextmanager

class DatabaseManager:
    """统一的数据库连接管理器"""

    def __init__(self, config: dict):
        self.config = config
        self._engine = None
        self._SessionLocal = None

    def _build_dsn(self) -> str:
        host = self.config.get("host", "127.0.0.1")
        port = self.config.get("port", 5432)
        user = self.config.get("username", "cjwdsg")
        password = self.config.get("password", "")
        database = self.config.get("database", "erp_simulation")
        return {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }

    @contextmanager
    def get_psycopg2_connection(self):
        """获取 psycopg2 连接（用于原生 SQL 执行）"""
        dsn = self._build_dsn()
        conn = psycopg2.connect(**dsn)
        try:
            yield conn
        finally:
            conn.close()

    def get_connection_info(self) -> dict:
        """获取当前连接信息（用于调试）"""
        return self._build_dsn()


# 全局实例（由 Container 管理，此处仅作为便捷回退）
_default_manager: Optional[DatabaseManager] = None


def get_default_manager() -> DatabaseManager:
    global _default_manager
    if _default_manager is None:
        from src.config import get_config
        _default_manager = DatabaseManager(get_config().get("database", {}))
    return _default_manager
```

- [ ] **Step 2: 修改 connection.py，将 get_monitor_connection 改为委托给 DatabaseManager**

```python
from .database import get_default_manager

def get_monitor_connection():
    """获取监控数据库连接（用于性能监控和 AI 分析）"""
    return get_default_manager().get_psycopg2_connection().__enter__()
```

- [ ] **Step 3: 修改 db.py，从 Depends 获取 connection info**

```python
# 替换原来 inline 的 get_db_config()
from src.core.dependencies import get_connection_manager

def get_db_config():
    return get_connection_manager().config  # Container 提供
```

- [ ] **Step 4: Commit**

```bash
git add backend/src/db/database.py backend/src/db/connection.py backend/src/db/manager.py backend/src/api/db.py
git commit -m "refactor: 统一数据库连接管理，消除 psycopg2 调用碎片化"
```

---

## Task 3: 拆分 text2sql God Module

**Files:**
- Create: `backend/src/api/text2sql/generate.py`
- Create: `backend/src/api/text2sql/explain.py`
- Modify: `backend/src/api/text2sql.py

- [ ] **Step 1: 创建 text2sql 包目录和 __init__.py**

```python
# backend/src/api/text2sql/__init__.py
from .generate import generate_sql
from .explain import execute_and_explain
```

- [ ] **Step 2: 提取 generate.py — NL→SQL 生成逻辑**

```python
"""
NL → SQL 生成
"""
from typing import Optional

def generate_sql(
    connection_id: str,
    query: str,
    llm_client,
    schema_introspector,
    template_manager
) -> dict:
    """生成 SQL 并返回结果"""
    # 原有 text2sql.py 中 generate 逻辑
    # ... 返回 {"success": True/False, "data": {...}, "error": "..."}
```

- [ ] **Step 3: 提取 explain.py — SQL 执行 + EXPLAIN**

```python
"""
SQL 执行与 EXPLAIN
"""
def execute_sql(connection_id: str, sql: str, limit: int = 1000) -> dict:
    """执行查询并返回结果"""
    # 原有 text2sql.py 中 execute 逻辑
    # ... 返回 {"columns": [...], "rows": [...], ...}

def explain_sql(connection_id: str, sql: str) -> dict:
    """执行 EXPLAIN 并返回计划"""
    # 原有 text2sql.py 中 explain 逻辑
    # ... 返回 {"success": True/False, "plan": "..."}
```

- [ ] **Step 4: 简化 text2sql.py 为路由编排层**

```python
# text2sql.py 只做: 路由 + 参数验证 + 调用子模块
# 删除所有生成/执行逻辑，保留 50 行以内
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/api/text2sql/
git commit -m "refactor: 拆分 text2sql.py 为 generate/explain 子模块"
```

---

## Task 4: 引入 PluginContext，解耦插件与连接

**Files:**
- Modify: `backend/src/plugins/base.py`
- Modify: `backend/src/plugins/builtin/query_executor.py`
- Modify: `backend/src/plugins/builtin/slow_query_analyzer.py`
- Modify: `backend/src/plugins/builtin/__init__.py`
- Modify: `backend/src/core/service.py`

- [ ] **Step 1: 定义 PluginContext 接口**

```python
# backend/src/plugins/base.py

class PluginContext:
    """插件执行上下文，提供插件所需的服务"""

    def __init__(self, db_manager, llm_client, config: dict):
        self.db_manager = db_manager
        self.llm_client = llm_client
        self.config = config

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        with self.db_manager.get_psycopg2_connection() as conn:
            yield conn


class DBATool(ABC):
    """DBA 工具基类"""

    @abstractmethod
    def execute(self, context: PluginContext, **params) -> ToolResult:
        """使用 PluginContext 执行工具"""
        pass
```

- [ ] **Step 2: 修改 QueryExecutor 使用 PluginContext**

```python
# plugins/builtin/query_executor.py

class QueryExecutor(DBATool):
    def execute(self, context: PluginContext, sql: str = None, **kwargs) -> ToolResult:
        with context.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            # ...
```

- [ ] **Step 3: 修改 SlowQueryAnalyzer 使用 PluginContext**

同上模式。

- [ ] **Step 4: 修改 service.py，传递 PluginContext 而非直接调用 registry**

```python
def process_message(self, message: str, context: PluginContext = None) -> dict:
    # 使用 context 而非 self.registry.get(tool_name)
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/plugins/base.py backend/src/plugins/builtin/query_executor.py backend/src/plugins/builtin/slow_query_analyzer.py backend/src/core/service.py
git commit -m "refactor: 引入 PluginContext 解耦插件与数据库连接"
```

---

## Task 5: 消除全局单例（ConnectionManager & TemplateManager）

**Files:**
- Modify: `backend/src/db/manager.py`
- Modify: `backend/src/db/template_manager.py`

- [ ] **Step 1: 移除 manager.py 的模块级 _manager 全局变量**

```python
# 替换全局单例为 Container 管理
# Container 已在 Task 1 中创建
```

- [ ] **Step 2: 移除 template_manager.py 的模块级 _template_manager 全局变量**

同上模式。

- [ ] **Step 3: 更新所有调用点，使用 Depends 而非直接调用 get_connection_manager()**

搜索所有 `from src.db.manager import get_connection_manager` 的调用，改为 `from src.core.dependencies import get_connection_manager`。

- [ ] **Step 4: Commit**

```bash
git add backend/src/db/manager.py backend/src/db/template_manager.py
git commit -m "refactor: 消除全局单例，统一由 Container 管理"
```

---

## Task 6: 统一错误处理策略

**Files:**
- Create: `backend/src/core/errors.py`
- Modify: `backend/src/core/llm.py`
- Modify: `backend/src/core/service.py`

- [ ] **Step 1: 创建统一的错误类层次**

```python
"""
DBA Assistant 错误类层次
"""
class DBAError(Exception):
    """基础错误类"""
    code: str = "DBA_ERROR"

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class LLMError(DBAError):
    code = "LLM_ERROR"


class DatabaseError(DBAError):
    code = "DATABASE_ERROR"


class ToolExecutionError(DBAError):
    code = "TOOL_ERROR"
```

- [ ] **Step 2: 修改 llm.py，使用统一的 LLMError**

```python
# 替换旧的 LLMError 为 core.errors.LLMError
```

- [ ] **Step 3: 在 main.py 添加全局异常处理器**

```python
from fastapi import Request
from src.core.errors import DBAError

@app.exception_handler(DBAError)
async def dba_error_handler(request: Request, exc: DBAError):
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": exc.message, "code": exc.code}
    )
```

- [ ] **Step 4: Commit**

```bash
git add backend/src/core/errors.py backend/src/core/llm.py backend/src/main.py
git commit -m "refactor: 建立统一的错误处理层次"
```

---

## Task 7: 合并 src/smart_assistant/ 到 backend/src/（可选，根据需要）

**前提:** Task 1-6 全部完成，架构清晰后再执行。

此任务将废弃 `src/smart_assistant/` 目录，将其独特功能迁移到 `backend/src/`，建立单一源码树。

---

## 验证清单

完成 Task 1-6 后，验证以下行为正常：

- [ ] `uvicorn src.main:app` 启动无错误
- [ ] `/api/chat/stream` 流式输出正常
- [ ] `/api/db/query` 查询返回正确数据
- [ ] `/api/monitor/analyze` AI 分析返回建议
- [ ] `/api/templates` 模板 CRUD 正常
- [ ] 无 `pytest` 测试失败（如果有测试的话）
