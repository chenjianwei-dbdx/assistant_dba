"""
内置文件操作工具
"""
import os
import glob
from pathlib import Path
from typing import Dict, Any, List

from ..base import BaseTool, ToolDefinition


class FileSearchTool(BaseTool):
    """文件搜索工具"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_search",
            description="在指定目录中搜索文件，支持按名称、扩展名搜索",
            category="file_ops",
            parameters=[
                {
                    "name": "directory",
                    "type": "string",
                    "required": True,
                    "description": "要搜索的目录路径"
                },
                {
                    "name": "pattern",
                    "type": "string",
                    "required": False,
                    "description": "文件名匹配模式（支持 glob，如 *.py）"
                },
                {
                    "name": "file_type",
                    "type": "string",
                    "required": False,
                    "description": "按文件扩展名过滤（如 py, js, txt）"
                }
            ],
            timeout=30
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        directory = kwargs.get("directory", ".")
        pattern = kwargs.get("pattern", "*")
        file_type = kwargs.get("file_type")

        # 验证目录
        if not os.path.isdir(directory):
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }

        # 构建搜索模式
        if file_type:
            search_pattern = f"*.{file_type}"
        else:
            search_pattern = pattern

        search_path = os.path.join(directory, "**", search_pattern)

        try:
            # 使用 glob 递归搜索
            files = glob.glob(search_path, recursive=True)

            # 限制结果数量
            max_results = 100
            if len(files) > max_results:
                files = files[:max_results]
                truncated = True
            else:
                truncated = False

            # 转换为相对路径
            files = [os.path.relpath(f, directory) for f in files]

            result = {
                "success": True,
                "files": files,
                "count": len(files),
                "truncated": truncated,
                "search_path": search_path
            }

            if truncated:
                result["note"] = f"结果已截断，仅显示前 {max_results} 个文件"

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }


class FileReadTool(BaseTool):
    """文件读取工具"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_read",
            description="读取文件内容",
            category="file_ops",
            parameters=[
                {
                    "name": "path",
                    "type": "string",
                    "required": True,
                    "description": "文件路径"
                },
                {
                    "name": "lines",
                    "type": "integer",
                    "required": False,
                    "default": 100,
                    "description": "最多读取的行数"
                }
            ],
            timeout=10
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        path = kwargs.get("path")
        max_lines = kwargs.get("lines", 100)

        if not os.path.isfile(path):
            return {
                "success": False,
                "error": f"File not found: {path}"
            }

        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip())

            content = "\n".join(lines)

            return {
                "success": True,
                "content": content,
                "path": path,
                "lines_read": len(lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Read failed: {str(e)}"
            }
