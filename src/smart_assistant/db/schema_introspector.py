"""
PostgreSQL Schema Introspector
自动获取数据库表结构，为 LLM 提供准确的 schema 信息，防止幻觉
"""
import psycopg2
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ColumnInfo:
    """列信息"""
    name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str]
    is_primary_key: bool
    is_foreign_key: bool
    foreign_table: Optional[str]
    foreign_column: Optional[str]
    comment: Optional[str]


@dataclass
class TableInfo:
    """表信息"""
    name: str
    schema: str
    comment: Optional[str]
    columns: List[ColumnInfo]
    primary_key: List[str]
    foreign_keys: List[Dict]


class SchemaIntrospector:
    """Schema  introspection for PostgreSQL"""

    def __init__(self, host: str, port: int, database: str, username: str, password: str):
        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": username,
            "password": password
        }

    def _connect(self):
        """建立数据库连接"""
        return psycopg2.connect(**self.connection_params)

    def get_all_tables(self, schema: str = "public") -> List[TableInfo]:
        """
        获取所有表的信息

        Args:
            schema: 数据库 schema，默认为 public

        Returns:
            表信息列表
        """
        tables = []
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                # 获取表信息
                cur.execute("""
                    SELECT
                        t.table_name,
                        t.table_schema,
                        obj_description(t.tableoid) as comment
                    FROM information_schema.tables t
                    WHERE t.table_schema = %s
                    AND t.table_type = 'BASE TABLE'
                    ORDER BY t.table_name
                """, (schema,))

                for row in cur.fetchall():
                    table_name, table_schema, comment = row
                    table_info = self._get_table_info(cur, table_name, table_schema, comment)
                    tables.append(table_info)
        finally:
            conn.close()

        return tables

    def _get_table_info(self, cur, table_name: str, schema: str, comment: str) -> TableInfo:
        """获取单个表的详细信息"""
        # 获取列信息
        cur.execute("""
            SELECT
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                col_description(format('%s.%s', c.table_schema, c.table_name)::regclass::oid, c.ordinal_position) as comment
            FROM information_schema.columns c
            WHERE c.table_schema = %s AND c.table_name = %s
            ORDER BY c.ordinal_position
        """, (schema, table_name))

        columns = []
        pk_columns = []

        for row in cur.fetchall():
            col_name, data_type, is_nullable, col_default, char_len, num_prec, num_scale, comment = row

            # 格式化数据类型
            if char_len:
                data_type = f"{data_type}({char_len})"
            elif num_prec is not None and num_scale is not None:
                data_type = f"{data_type}({num_prec},{num_scale})"

            # 检查是否是主键
            is_pk = self._is_primary_key(cur, schema, table_name, col_name)
            if is_pk:
                pk_columns.append(col_name)

            # 检查是否是外键
            is_fk, fk_table, fk_column = self._get_foreign_key_info(cur, schema, table_name, col_name)

            columns.append(ColumnInfo(
                name=col_name,
                data_type=data_type,
                is_nullable=(is_nullable == 'YES'),
                column_default=col_default,
                is_primary_key=is_pk,
                is_foreign_key=is_fk,
                foreign_table=fk_table,
                foreign_column=fk_column,
                comment=comment
            ))

        # 获取外键信息
        foreign_keys = self._get_table_foreign_keys(cur, schema, table_name)

        return TableInfo(
            name=table_name,
            schema=schema,
            comment=comment,
            columns=columns,
            primary_key=pk_columns,
            foreign_keys=foreign_keys
        )

    def _is_primary_key(self, cur, schema: str, table_name: str, column_name: str) -> bool:
        """检查是否是主键"""
        cur.execute("""
            SELECT 1 FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s
                AND kcu.column_name = %s
        """, (schema, table_name, column_name))
        return cur.fetchone() is not None

    def _get_foreign_key_info(self, cur, schema: str, table_name: str, column_name: str):
        """获取外键信息"""
        cur.execute("""
            SELECT
                kcu.table_name AS foreign_table,
                kcu.column_name AS foreign_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s
                AND kcu.column_name = %s
        """, (schema, table_name, column_name))
        result = cur.fetchone()
        if result:
            return True, result[0], result[1]
        return False, None, None

    def _get_table_foreign_keys(self, cur, schema: str, table_name: str) -> List[Dict]:
        """获取表的所有外键"""
        cur.execute("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
                AND tc.table_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s
        """, (schema, table_name))
        return [
            {"column": row[0], "foreign_table": row[1], "foreign_column": row[2]}
            for row in cur.fetchall()
        ]

    def generate_schema_summary(self, schema: str = "public") -> str:
        """
        生成用于 LLM 的 schema 总结

        Returns:
            格式化的 schema 描述字符串
        """
        tables = self.get_all_tables(schema)

        if not tables:
            return "数据库中没有表"

        lines = ["## 数据库 Schema 信息\n"]

        for table in tables:
            # 表头
            lines.append(f"### 表: {table.name}")
            if table.comment:
                lines.append(f"说明: {table.comment}")
            lines.append("")

            # 列信息
            lines.append("| 列名 | 类型 | 可空 | 说明 |")
            lines.append("|------|------|------|------|")

            for col in table.columns:
                nullable = "否" if not col.is_nullable else "是"
                pk = " (PK)" if col.is_primary_key else ""
                fk = f" (FK → {col.foreign_table}.{col.foreign_column})" if col.is_foreign_key else ""
                comment = col.comment or ""
                lines.append(f"| {col.name} | {col.data_type}{pk}{fk} | {nullable} | {comment} |")

            # 外键关系
            if table.foreign_keys:
                lines.append("")
                lines.append("外键关系:")
                for fk in table.foreign_keys:
                    lines.append(f"- {table.name}.{fk['column']} → {fk['foreign_table']}.{fk['foreign_column']}")

            lines.append("")

        return "\n".join(lines)

    def validate_table_exists(self, table_name: str, schema: str = "public") -> bool:
        """验证表是否存在"""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                """, (schema, table_name))
                return cur.fetchone() is not None
        finally:
            conn.close()

    def validate_column_exists(self, table_name: str, column_name: str, schema: str = "public") -> bool:
        """验证列是否存在"""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s AND column_name = %s
                """, (schema, table_name, column_name))
                return cur.fetchone() is not None
        finally:
            conn.close()
