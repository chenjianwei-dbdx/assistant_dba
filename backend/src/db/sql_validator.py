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
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(r'\b' + pattern + r'\b', sql_upper):
                return False, pattern
        return True, ""
