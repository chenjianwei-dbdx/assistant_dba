"""
Index Analyzer Plugin
索引分析插件
"""
from typing import Dict, List
from ..base import DBATool, ToolResult
from src.db.connection import get_monitor_connection


class IndexAnalyzer(DBATool):
    """索引健康分析器"""

    @property
    def name(self) -> str:
        return "index_analyzer"

    @property
    def description(self) -> str:
        return "分析数据库索引健康状态，找出未使用或冗余的索引"

    @property
    def parameters(self) -> list:
        return [
            {
                "name": "connection_id",
                "type": "string",
                "required": False,
                "description": "数据库连接 ID（可选）"
            },
            {
                "name": "table_name",
                "type": "string",
                "required": False,
                "description": "指定分析的数据表（不填则分析所有表）"
            },
            {
                "name": "action",
                "type": "string",
                "required": False,
                "enum": ["all", "unused", "missing", "duplicate"],
                "description": "分析类型"
            }
        ]

    def execute(self, **kwargs) -> ToolResult:
        table_name = kwargs.get("table_name")
        action = kwargs.get("action", "all")

        try:
            if action == "unused":
                return self._find_unused_indexes(table_name)
            elif action == "missing":
                return self._find_missing_indexes(table_name)
            elif action == "duplicate":
                return self._find_duplicate_indexes(table_name)
            else:
                return self._analyze_all_indexes(table_name)
        except Exception as e:
            return ToolResult(success=False, error=f"索引分析失败: {str(e)}")

    def _analyze_all_indexes(self, table_name: str = None) -> ToolResult:
        """分析所有索引"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            where_clause = "AND t.relname = %s" if table_name else ""
            params = (table_name,) if table_name else None

            # 查询索引使用情况
            cur.execute(f"""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                {where_clause}
                ORDER BY tablename, indexname
            """, params)

            unused_indexes = []
            low_usage_indexes = []
            all_indexes = []

            for row in cur.fetchall():
                index_info = {
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "scans": row[3],
                    "rows_read": row[4],
                    "rows_fetched": row[5],
                    "size": row[6]
                }
                all_indexes.append(index_info)

                if row[3] == 0:
                    unused_indexes.append(index_info)
                elif row[3] < 100:
                    low_usage_indexes.append(index_info)

            # 查询缺失索引（高频更新的表）
            cur.execute("""
                SELECT
                    schemaname,
                    relname,
                    seq_scan,
                    n_tup_ins + n_tup_upd + n_tup_del as total_writes,
                    n_live_tup + n_dead_tup as total_rows
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                AND seq_scan > 1000
                ORDER BY seq_scan DESC
                LIMIT 10
            """)

            missing_indexes = []
            for row in cur.fetchall():
                missing_indexes.append({
                    "schema": row[0],
                    "table": row[1],
                    "seq_scans": row[2],
                    "total_writes": row[3],
                    "total_rows": row[4],
                    "suggestion": f"表 {row[1]} 全表扫描次数过多，建议分析查询模式并添加适当索引"
                })

            cur.close()
            conn.close()

            return ToolResult(
                success=True,
                output={
                    "all_indexes": all_indexes,
                    "unused_indexes": unused_indexes,
                    "low_usage_indexes": low_usage_indexes,
                    "missing_indexes": missing_indexes[:10]
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _find_unused_indexes(self, table_name: str = None) -> ToolResult:
        """查找未使用的索引"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            where_clause = "AND tablename = %s" if table_name else ""
            params = (table_name,) if table_name else None

            cur.execute(f"""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    pg_relation_size(indexrelid) as index_size_bytes,
                    indexdef
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                AND schemaname = 'public'
                {where_clause}
                ORDER BY pg_relation_size(indexrelid) DESC
            """, params)

            unused = []
            for row in cur.fetchall():
                unused.append({
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "size_bytes": row[3],
                    "size": f"{row[3] / 1024:.1f} KB",
                    "definition": row[4],
                    "suggestion": f"索引 {row[2]} 从未使用，可以考虑删除以减少写入开销"
                })

            cur.close()
            conn.close()

            return ToolResult(success=True, output={"unused_indexes": unused})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _find_missing_indexes(self, table_name: str = None) -> ToolResult:
        """查找可能缺失的索引"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            where_clause = "AND relname = %s" if table_name else ""
            params = (table_name,) if table_name else None

            # 找出高频全表扫描且写操作多的表
            cur.execute(f"""
                SELECT
                    schemaname,
                    relname,
                    seq_scan,
                    idx_scan,
                    seq_tup_read,
                    idx_tup_fetch,
                    n_tup_ins + n_tup_upd + n_tup_del as total_writes
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                AND seq_scan > idx_scan * 10
                AND seq_scan > 1000
                {where_clause}
                ORDER BY seq_scan DESC
                LIMIT 20
            """, params)

            missing = []
            for row in cur.fetchall():
                idx_ratio = (row[4] / (row[4] + row[5]) * 100) if (row[4] + row[5]) > 0 else 0
                missing.append({
                    "schema": row[0],
                    "table": row[1],
                    "seq_scans": row[2],
                    "index_scans": row[3],
                    "seq_rows_read": row[4],
                    "index_rows_fetched": row[5],
                    "total_writes": row[6],
                    "seq_scan_ratio_pct": round(idx_ratio, 1),
                    "suggestion": f"全表扫描占比 {idx_ratio:.1f}%，建议检查 WHERE/JOIN 条件添加索引"
                })

            cur.close()
            conn.close()

            return ToolResult(success=True, output={"missing_indexes": missing})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _find_duplicate_indexes(self, table_name: str = None) -> ToolResult:
        """查找重复索引"""
        try:
            conn = get_monitor_connection()
            cur = conn.cursor()

            where_clause = "AND t.relname = %s" if table_name else ""
            params = (table_name,) if table_name else None

            # 查找同一表上索引列相同的重复索引
            cur.execute(f"""
                SELECT
                    schemaname,
                    relname,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                {where_clause}
                ORDER BY relname, indexname
            """, params)

            from collections import defaultdict
            index_by_table = defaultdict(list)
            for row in cur.fetchall():
                index_by_table[row[1]].append({
                    "index": row[2],
                    "definition": row[3]
                })

            duplicates = []
            for table, indexes in index_by_table.items():
                # 简单检测：比较 indexdef
                seen = {}
                for idx in indexes:
                    cols = self._extract_index_columns(idx["definition"])
                    key = tuple(sorted(cols))
                    if key in seen:
                        duplicates.append({
                            "schema": "public",
                            "table": table,
                            "index1": seen[key],
                            "index2": idx["index"],
                            "columns": cols,
                            "suggestion": f"索引 {seen[key]} 和 {idx['index']} 索引列相同，可能重复"
                        })
                    else:
                        seen[key] = idx["index"]

            cur.close()
            conn.close()

            return ToolResult(success=True, output={"duplicate_indexes": duplicates})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _extract_index_columns(self, indexdef: str) -> List[str]:
        """从索引定义中提取列名"""
        import re
        # 匹配 CREATE INDEX ... ON table (col1, col2, ...)
        match = re.search(r'ON \w+ \(([^)]+)\)', indexdef)
        if match:
            cols = match.group(1).split(',')
            return [c.strip().split(' ')[0].strip('"') for c in cols]
        return []
