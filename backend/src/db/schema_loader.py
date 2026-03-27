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