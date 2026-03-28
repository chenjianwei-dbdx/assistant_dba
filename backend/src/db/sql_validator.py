"""
SQL Validator
SQL 验证层：语法验证、表名验证、危险操作检查
"""
import re
from typing import List, Set, Tuple, Optional
from dataclasses import dataclass, field
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
    extracted_tables: List[str] = field(default_factory=list)

    @classmethod
    def success(cls, tables: List[str] = None) -> 'ValidationResult':
        return cls(valid=True, extracted_tables=tables or [])

    @classmethod
    def failure(cls, error: str) -> 'ValidationResult':
        return cls(valid=False, error=error)


class SQLValidator:
    """SQL 验证器"""

    # 允许的系统表/视图（pg_ 和 pg_stat_ 前缀的系统表）
    SYSTEM_TABLES = {
        # pg_ 系统目录表
        'pg_am', 'pg_attribute', 'pg_authid', 'pg_auth_members', 'pg_cast',
        'pg_class', 'pg_constraint', 'pg_database', 'pg_depend', 'pg_description',
        'pg_enum', 'pg_extension', 'pg_foreign_data_wrapper', 'pg_foreign_server',
        'pg_index', 'pg_inherits', 'pg_language', 'pg_largeobject', 'pg_namespace',
        'pg_opclass', 'pg_operator', 'pg_opfamily', 'pg_proc', 'pg_range',
        'pg_rewrite', 'pg_settings', 'pg_shdepend', 'pg_shdescription', 'pg_statistic',
        'pg_tablespace', 'pg_trigger', 'pg_type', 'pg_user_mapping',
        # pg_stat_ 统计视图
        'pg_stat_activity', 'pg_stat_bgwriter', 'pg_stat_database', 'pg_stat_gssapi',
        'pg_stat_progress_vacuum', 'pg_stat_replication', 'pg_stat_slru', 'pg_stat_subscription',
        'pg_stat_sys_tables', 'pg_stat_user_tables', 'pg_stat_user_indexes', 'pg_stat_statements',
        'pg_stat_progress_cluster', 'pg_stat_progress_vacuum', 'pg_statio_user_tables',
        'pg_statio_user_indexes', 'pg_statio_sys_tables', 'pg_statio_sys_indexes',
        'pg_stat_archiver', 'pg_stat_wal_receiver', 'pg_replication_slots',
        # information_schema
        'information_schema.tables', 'information_schema.columns', 'information_schema.views',
        'information_schema.routines', 'information_schema.table_constraints',
        'information_schema.key_column_usage',
    }

    # 危险操作关键词
    DANGEROUS_PATTERNS = [
        'DROP', 'TRUNCATE', 'ALTER', 'DELETE', 'INSERT', 'UPDATE',
        'CREATE', 'GRANT', 'REVOKE', 'EXECUTE', 'COPY', 'PG_READ_FILE',
        'PG_WRITE_FILE', 'LO_IMPORT', 'LO_EXPORT'
    ]

    def __init__(self):
        pass

    def validate(self, sql: str, valid_tables: List[str]) -> ValidationResult:
        """验证 SQL"""
        if not sql or not sql.strip():
            return ValidationResult.failure("SQL 不能为空")

        # 1. 语法验证
        syntax_result = self.validate_syntax(sql)
        if not syntax_result[0]:
            return ValidationResult.failure(f"SQL 语法错误: {syntax_result[1]}")

        # 2. 提取并验证表名
        extracted_tables = self.extract_tables(sql)
        for table in extracted_tables:
            # 跳过系统表校验
            if table in self.SYSTEM_TABLES or table.startswith('pg_') or table.startswith('information_schema.'):
                continue
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
                return True, ""
            except Exception as e:
                return False, str(e)
        else:
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith('SELECT'):
                return False, "只允许 SELECT 查询"
            return True, ""

    def extract_tables(self, sql: str) -> List[str]:
        """从 SQL 中提取表名"""
        tables = set()
        # 支持 dotted 名称 (schema.table, information_schema.tables)
        dotted_pattern = r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
        single_pattern = r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        join_pattern = r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
        patterns = [dotted_pattern, single_pattern, join_pattern]
        sql_upper = sql.upper()
        for pattern in patterns:
            matches = re.findall(pattern, sql_upper, re.IGNORECASE)
            tables.update([m.lower() for m in matches])
        return list(tables)

    def check_dangerous_operations(self, sql: str) -> Tuple[bool, str]:
        """检查危险操作"""
        sql_upper = sql.upper()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(r'\b' + pattern + r'\b', sql_upper):
                return False, pattern
        return True, ""
