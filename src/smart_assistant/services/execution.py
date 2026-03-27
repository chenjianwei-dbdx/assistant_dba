"""
工具执行服务模块
"""
import time
from typing import Dict, Any
from ..tools.registry import ToolRegistry


class ExecutionService:
    """工具执行服务"""

    def __init__(self, tool_registry: ToolRegistry):
        """
        初始化执行服务

        Args:
            tool_registry: 工具注册表
        """
        self.tool_registry = tool_registry

    def execute(self, tool_name: str, params: Dict) -> Dict[str, Any]:
        """
        执行工具

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            执行结果
        """
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
                "tool_name": tool_name
            }

        # 验证参数
        is_valid, missing, invalid = tool.validate_params(**params)
        if not is_valid:
            if missing:
                return {
                    "success": False,
                    "error": f"Missing required parameters: {missing}",
                    "tool_name": tool_name,
                    "missing_params": missing
                }
            if invalid:
                return {
                    "success": False,
                    "error": f"Invalid parameters: {invalid}",
                    "tool_name": tool_name
                }

        # 执行工具
        start_time = time.time()
        try:
            result = tool.execute(**params)
            execution_time = int((time.time() - start_time) * 1000)

            # 特殊处理 SQL Query 工具的结果
            if tool_name == "sql_query":
                output = self._format_sql_result(result)
                return {
                    "success": result.get("success", False),
                    "output": output,
                    "error": result.get("error", ""),
                    "tool_name": tool_name,
                    "execution_time_ms": execution_time,
                    "sql": result.get("sql", ""),
                    "row_count": result.get("row_count", 0),
                    "columns": result.get("columns", [])
                }

            return {
                "success": result.get("success", False),
                "output": result.get("output", result.get("stdout", "")),
                "error": result.get("error", result.get("stderr", "")),
                "tool_name": tool_name,
                "execution_time_ms": execution_time,
                "returncode": result.get("returncode")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "tool_name": tool_name,
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }

    def _format_sql_result(self, result: Dict) -> str:
        """格式化 SQL 查询结果"""
        if not result.get("success"):
            return f"查询失败: {result.get('error', '未知错误')}\n\nSQL: {result.get('sql', '')}"

        sql = result.get("sql", "")
        columns = result.get("columns", [])
        rows = result.get("results", [])
        row_count = result.get("row_count", 0)
        truncated = result.get("truncated", False)

        lines = []
        lines.append(f"**SQL 查询:**\n```sql\n{sql}\n```\n")
        lines.append(f"**执行结果:** 返回 {row_count} 行")

        if truncated:
            lines.append(f"（结果被截断，仅显示前 {len(rows)} 行）")

        if not rows:
            return "\n".join(lines)

        lines.append("")

        # 构建表格
        col_widths = [len(c) for c in columns]
        for row in rows:
            for i, val in enumerate(row):
                val_str = str(val) if val is not None else "NULL"
                col_widths[i] = max(col_widths[i], min(len(val_str), 50))

        # 表头
        header = " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(columns))
        separator = "-|-".join("-" * w for w in col_widths)

        lines.append("| " + header + " |")
        lines.append("| " + separator.replace("-", "-") + " |")

        # 数据行（最多 20 行）
        for row in rows[:20]:
            row_vals = []
            for i, val in enumerate(row):
                val_str = str(val) if val is not None else "NULL"
                if len(val_str) > 50:
                    val_str = val_str[:47] + "..."
                row_vals.append(val_str.ljust(col_widths[i]))
            lines.append("| " + " | ".join(row_vals) + " |")

        return "\n".join(lines)

    def validate_tool_exists(self, tool_name: str) -> bool:
        """
        验证工具是否存在

        Args:
            tool_name: 工具名称

        Returns:
            是否存在
        """
        return self.tool_registry.get_tool(tool_name) is not None

    def list_available_tools(self) -> list:
        """
        列出所有可用工具

        Returns:
            工具信息列表
        """
        tools = self.tool_registry.list_tools()
        return [
            {
                "name": tool.definition.name,
                "description": tool.definition.description,
                "category": tool.definition.category,
                "parameters": tool.definition.parameters
            }
            for tool in tools
        ]
