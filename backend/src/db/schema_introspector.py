"""
Schema Introspector
从数据库动态获取表结构信息
"""
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy import inspect, MetaData
from sqlalchemy.engine import Engine


@dataclass
class ColumnInfo:
    """列信息"""
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_table: Optional[str] = None
    foreign_column: Optional[str] = None
    comment: Optional[str] = None


@dataclass
class TableInfo:
    """表信息"""
    name: str
    columns: List[ColumnInfo]
    comment: Optional[str] = None


class SchemaIntrospector:
    """Schema  introspector - 从数据库获取表结构"""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = inspect(engine)
        self.metadata = MetaData()
        self.metadata.reflect(bind=engine)

    def get_all_tables(self) -> List[TableInfo]:
        """获取所有表的信息"""
        tables = []
        for table_name in self.inspector.get_table_names():
            table_info = self._get_table_info(table_name)
            if table_info:
                tables.append(table_info)
        return tables

    def _get_table_info(self, table_name: str) -> Optional[TableInfo]:
        """获取单个表的详细信息"""
        try:
            # 获取主键
            primary_keys = set(self.inspector.get_pk_constraint(table_name).get('constrained_columns', []))

            # 获取外键
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            fk_map = {}
            for fk in foreign_keys:
                for col in fk.get('constrained_columns', []):
                    fk_map[col] = (fk.get('referred_table'), fk.get('referred_columns', []))

            # 获取列信息
            columns = []
            for col in self.inspector.get_columns(table_name):
                col_name = col['name']
                is_pk = col_name in primary_keys
                is_fk = col_name in fk_map

                if is_fk:
                    foreign_table, foreign_cols = fk_map[col_name]
                    foreign_col = foreign_cols[0] if foreign_cols else None
                else:
                    foreign_table = None
                    foreign_col = None

                column_info = ColumnInfo(
                    name=col_name,
                    data_type=str(col['type']),
                    is_nullable=col['nullable'],
                    is_primary_key=is_pk,
                    is_foreign_key=is_fk,
                    foreign_table=foreign_table,
                    foreign_column=foreign_col,
                    comment=col.get('comment')
                )
                columns.append(column_info)

            return TableInfo(name=table_name, columns=columns)

        except Exception:
            return None

    def get_table_names(self) -> List[str]:
        """获取所有表名"""
        return self.inspector.get_table_names()
