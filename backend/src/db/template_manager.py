"""
SQL Template Manager
SQL 模板管理器
"""
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path


# 默认模板路径
DEFAULT_TEMPLATE_FILE = Path(__file__).parent.parent.parent.parent / "configs" / "sql_templates.json"


class SQLTemplate:
    """SQL 模板"""

    def __init__(
        self,
        id: int = None,
        name: str = "",
        category: str = "",
        description: str = "",
        sql_pattern: str = "",
        parameters: List[Dict] = None,
        examples: str = "",
        use_count: int = 0,
        is_favorite: bool = False,
        created_at: str = None,
        updated_at: str = None
    ):
        self.id = id
        self.name = name
        self.category = category
        self.description = description
        self.sql_pattern = sql_pattern
        self.parameters = parameters or []
        self.examples = examples
        self.use_count = use_count
        self.is_favorite = is_favorite
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "sql_pattern": self.sql_pattern,
            "parameters": self.parameters,
            "examples": self.examples,
            "use_count": self.use_count,
            "is_favorite": self.is_favorite,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SQLTemplate":
        return cls(**d)


class TemplateManager:
    """模板管理器"""

    # 内置默认模板（DBA 常用查询）
    DEFAULT_TEMPLATES = [
        # Performance - AWR 类
        {
            "name": "AWR-TopSQL(耗时)",
            "category": "performance",
            "description": "按总执行耗时排序的 Top SQL，类似 Oracle AWR 报告",
            "sql_pattern": """
SELECT query,
       calls,
       total_exec_time,
       mean_exec_time,
       (total_exec_time / NULLIF(calls, 0))::bigint as avg_ms,
       rows,
       shared_blks_hit,
       shared_blks_read,
       shared_blks Dirtied,
       shared_blks Written
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT {limit};
            """.strip(),
            "parameters": [
                {"name": "limit", "type": "integer", "default": 20, "description": "返回条数"}
            ],
            "examples": "查看耗时最长的 20 条 SQL"
        },
        {
            "name": "AWR-TopSQL(平均耗时)",
            "category": "performance",
            "description": "按平均执行耗时排序的 Top SQL",
            "sql_pattern": """
SELECT query,
       calls,
       mean_exec_time,
       max_exec_time,
       min_exec_time,
       rows,
       shared_blks_hit,
       shared_blks_read
FROM pg_stat_statements
WHERE calls >= {min_calls}
ORDER BY mean_exec_time DESC
LIMIT {limit};
            """.strip(),
            "parameters": [
                {"name": "limit", "type": "integer", "default": 20, "description": "返回条数"},
                {"name": "min_calls", "type": "integer", "default": 5, "description": "最小调用次数"}
            ],
            "examples": "查看平均耗时最长的 SQL（调用次数>=5）"
        },
        {
            "name": "AWR-TopSQL(Buffer)",
            "category": "performance",
            "description": "按 Buffer I/O 排序的 Top SQL",
            "sql_pattern": """
SELECT query,
       calls,
       shared_blks_hit,
       shared_blks_read,
       (shared_blks_hit + shared_blks_read) as total_buffer_gets,
       ROUND((shared_blks_hit::numeric / NULLIF(shared_blks_hit + shared_blks_read, 0)) * 100, 1) as hit_ratio
FROM pg_stat_statements
ORDER BY (shared_blks_hit + shared_blks_read) DESC
LIMIT {limit};
            """.strip(),
            "parameters": [
                {"name": "limit", "type": "integer", "default": 20, "description": "返回条数"}
            ],
            "examples": "查看 Buffer 消耗最多的 SQL"
        },
        {
            "name": "慢查询列表",
            "category": "slow_query",
            "description": "执行时间超过阈值的查询",
            "sql_pattern": """
SELECT query,
       calls,
       mean_exec_time,
       max_exec_time,
       min_exec_time,
       total_exec_time,
       rows
FROM pg_stat_statements
WHERE mean_exec_time >= {threshold_ms}
ORDER BY mean_exec_time DESC
LIMIT {limit};
            """.strip(),
            "parameters": [
                {"name": "threshold_ms", "type": "integer", "default": 100, "description": "耗时阈值(ms)"},
                {"name": "limit", "type": "integer", "default": 20, "description": "返回条数"}
            ],
            "examples": "查看超过 100ms 的慢查询"
        },
        {
            "name": "表扫描统计",
            "category": "table_stats",
            "description": "按全表扫描次数排序的表统计",
            "sql_pattern": """
SELECT schemaname,
       relname as table_name,
       seq_scan,
       seq_tup_read,
       idx_scan,
       idx_tup_fetch,
       n_tup_ins,
       n_tup_upd,
       n_tup_del,
       n_live_tup,
       n_dead_tup,
       ROUND(idx_scan::numeric / NULLIF(seq_scan + idx_scan, 0) * 100, 1) as idx_scan_ratio
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY seq_scan DESC
LIMIT {limit};
            """.strip(),
            "parameters": [
                {"name": "limit", "type": "integer", "default": 20, "description": "返回条数"}
            ],
            "examples": "查看全表扫描最多的表"
        },
        {
            "name": "索引使用统计",
            "category": "index_stats",
            "description": "按扫描次数排序的索引统计",
            "sql_pattern": """
SELECT schemaname,
       relname as table_name,
       indexrelname as index_name,
       idx_scan,
       idx_tup_read,
       idx_tup_fetch,
       pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC
LIMIT {limit};
            """.strip(),
            "parameters": [
                {"name": "limit", "type": "integer", "default": 20, "description": "返回条数"}
            ],
            "examples": "查看使用最多的索引"
        },
        {
            "name": "未使用索引",
            "category": "index_stats",
            "description": "从未被扫描过的索引",
            "sql_pattern": """
SELECT schemaname,
       relname as table_name,
       indexrelname as index_name,
       pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
       indexdef
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
            """.strip(),
            "parameters": [],
            "examples": "找出从未使用的索引"
        },
        {
            "name": "死亡元组检测",
            "category": "vacuum",
            "description": "死亡元组过多的表",
            "sql_pattern": """
SELECT schemaname,
       relname as table_name,
       n_live_tup,
       n_dead_tup,
       n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100 as dead_tuple_ratio,
       last_vacuum,
       last_autovacuum,
       vacuum_count,
       autovacuum_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
AND n_dead_tup > {threshold}
ORDER BY n_dead_tup DESC;
            """.strip(),
            "parameters": [
                {"name": "threshold", "type": "integer", "default": 100, "description": "死亡元组阈值"}
            ],
            "examples": "查看死亡元组超过 100 的表"
        },
        {
            "name": "VACUUM 建议",
            "category": "vacuum",
            "description": "需要执行 VACUUM 的表",
            "sql_pattern": """
SELECT
    schemaname || '.' || relname as table_name,
    n_dead_tup,
    last_autovacuum,
    autovacuum_count,
    CASE
        WHEN n_dead_tup > 10000 THEN '急需 VACUUM'
        WHEN n_dead_tup > 1000 THEN '建议 VACUUM'
        ELSE '正常'
    END as recommend,
    'VACUUM ANALYZE ' || schemaname || '.' || relname as suggest_sql
FROM pg_stat_user_tables
WHERE schemaname = 'public'
AND n_dead_tup > 0
ORDER BY n_dead_tup DESC;
            """.strip(),
            "parameters": [],
            "examples": "查看需要 VACUUM 的表"
        },
        {
            "name": "连接状态",
            "category": "connection",
            "description": "当前数据库连接状态",
            "sql_pattern": """
SELECT
    state,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (now() - query_start)) as avg_duration_sec
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state
ORDER BY count DESC;
            """.strip(),
            "parameters": [],
            "examples": "查看当前连接状态"
        },
        {
            "name": "活跃连接详情",
            "category": "connection",
            "description": "当前正在执行的查询",
            "sql_pattern": """
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query,
    state_change,
    EXTRACT(EPOCH FROM (now() - query_start)) as duration_sec,
    wait_event
FROM pg_stat_activity
WHERE datname = current_database()
AND state = 'active'
AND query_start < now() - interval '1 second'
ORDER BY query_start;
            """.strip(),
            "parameters": [],
            "examples": "查看正在执行的查询"
        },
        {
            "name": "长事务",
            "category": "connection",
            "description": "运行时间过长的事务",
            "sql_pattern": """
SELECT
    pid,
    usename,
    application_name,
    state,
    query_start,
    EXTRACT(EPOCH FROM (now() - xact_start)) as xact_duration_sec,
    state_change,
    ROW_NUMBER() OVER(PARTITION BY state ORDER BY xact_start) as rn
FROM pg_stat_activity
WHERE datname = current_database()
AND xact_start IS NOT NULL
AND state <> 'idle'
AND now() - xact_start > interval '1 minute'
ORDER BY xact_start;
            """.strip(),
            "parameters": [],
            "examples": "查看超过 1 分钟的长事务"
        },
        {
            "name": "数据库统计概览",
            "category": "database",
            "description": "数据库整体统计信息",
            "sql_pattern": """
SELECT
    numbackends as connections,
    xact_commit,
    xact_rollback,
    blks_hit,
    blks_read,
    ROUND(blks_hit::numeric / NULLIF(blks_hit + blks_read, 0) * 100, 2) as cache_hit_ratio,
    tup_returned,
    tup_fetched,
    tup_inserted,
    tup_updated,
    tup_deleted
FROM pg_stat_database
WHERE datname = current_database();
            """.strip(),
            "parameters": [],
            "examples": "查看数据库统计概览"
        },
        {
            "name": "表大小排行",
            "category": "table_stats",
            "description": "按大小排序的表",
            "sql_pattern": """
SELECT
    schemaname,
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname) - pg_relation_size(schemaname||'.'||relname)) as indexes_size,
    n_live_tup + n_dead_tup as total_rows
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC
LIMIT {limit};
            """.strip(),
            "parameters": [
                {"name": "limit", "type": "integer", "default": 20, "description": "返回条数"}
            ],
            "examples": "查看最大的 20 张表"
        },
        {
            "name": "索引膨胀检测",
            "category": "index_stats",
            "description": "检测可能膨胀的索引",
            "sql_pattern": """
SELECT
    schemaname,
    relname as table_name,
    indexrelname as index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan,
    ROUND((pg_relation_size(indexrelid)::numeric / NULLIF(n_live_tup, 0) * 100, 2) as index_row_ratio
FROM pg_stat_user_indexes i
JOIN pg_stat_user_tables t ON i.relid = t.relid
WHERE schemaname = 'public'
AND idx_scan < 100
AND pg_relation_size(indexrelid) > 1024 * 1024
ORDER BY pg_relation_size(indexrelid) DESC;
            """.strip(),
            "parameters": [],
            "examples": "检测索引膨胀"
        }
    ]

    def __init__(self, templates_file: str = None):
        self.templates_file = Path(templates_file) if templates_file else DEFAULT_TEMPLATE_FILE
        self._templates: Dict[int, SQLTemplate] = {}
        self._next_id = 1
        self._load()

    def _load(self):
        """加载模板"""
        if self.templates_file.exists():
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    # 如果没有 id，自动分配
                    if 'id' not in item:
                        item['id'] = self._next_id
                    t = SQLTemplate.from_dict(item)
                    self._templates[t.id] = t
                    if t.id >= self._next_id:
                        self._next_id = t.id + 1
        else:
            # 初始化默认模板
            self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认模板"""
        for item in self.DEFAULT_TEMPLATES:
            self.add_template(item)

    def _save(self):
        """保存模板"""
        self.templates_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            templates = [t.to_dict() for t in self._templates.values()]
            json.dump(templates, f, ensure_ascii=False, indent=2)

    def add_template(self, data: dict) -> SQLTemplate:
        """添加模板"""
        t = SQLTemplate(
            id=self._next_id,
            name=data["name"],
            category=data["category"],
            description=data.get("description", ""),
            sql_pattern=data["sql_pattern"],
            parameters=data.get("parameters", []),
            examples=data.get("examples", ""),
            use_count=0,
            is_favorite=False
        )
        self._templates[t.id] = t
        self._next_id += 1
        self._save()
        return t

    def update_template(self, id: int, data: dict) -> Optional[SQLTemplate]:
        """更新模板"""
        if id not in self._templates:
            return None
        t = self._templates[id]
        for key in ["name", "category", "description", "sql_pattern", "parameters", "examples", "is_favorite"]:
            if key in data:
                setattr(t, key, data[key])
        t.updated_at = datetime.now().isoformat()
        self._save()
        return t

    def delete_template(self, id: int) -> bool:
        """删除模板"""
        if id in self._templates:
            del self._templates[id]
            self._save()
            return True
        return False

    def get_template(self, id: int) -> Optional[SQLTemplate]:
        """获取模板"""
        return self._templates.get(id)

    def list_templates(self, category: str = None, keyword: str = None) -> List[SQLTemplate]:
        """列出模板"""
        result = list(self._templates.values())
        if category:
            result = [t for t in result if t.category == category]
        if keyword:
            keyword = keyword.lower()
            result = [t for t in result if keyword in t.name.lower() or keyword in t.description.lower()]
        return result

    def list_categories(self) -> List[str]:
        """列出所有分类"""
        cats = set(t.category for t in self._templates.values())
        return sorted(cats)

    def increment_use_count(self, id: int):
        """增加使用次数"""
        if id in self._templates:
            self._templates[id].use_count += 1
            self._save()

    def fill_parameters(self, sql_pattern: str, params: dict, template_params: list = None) -> str:
        """填充参数到 SQL 模板

        Args:
            sql_pattern: SQL模板
            params: 用户提供的参数
            template_params: 模板参数定义列表（含 default 值）
        """
        result = sql_pattern

        # 构建默认值映射
        defaults = {}
        if template_params:
            for p in template_params:
                if isinstance(p, dict) and 'name' in p:
                    defaults[p['name']] = p.get('default')

        # 填充参数（用户提供的值优先，否则用默认值）
        for key, value in params.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        # 填充未提供的参数（使用默认值）
        for key, default_value in defaults.items():
            placeholder = "{" + key + "}"
            if placeholder in result and default_value is not None:
                result = result.replace(placeholder, str(default_value))

        # 清理仍未填充的参数（去掉占位符）
        import re
        result = re.sub(r'\{[^}]+\}', '', result)
        return result


