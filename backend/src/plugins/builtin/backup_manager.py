"""
Backup Manager Plugin
备份管理插件
"""
import os
import subprocess
import shutil
from datetime import datetime
from typing import Dict, List
from pathlib import Path
from ..base import DBATool, ToolResult
from src.config import get_config


class BackupManager(DBATool):
    """数据库备份管理器"""

    def __init__(self):
        super().__init__()
        config = get_config()
        self.backup_dir = config.get("backup", {}).get("path", "/tmp/postgres_backups")

    @property
    def name(self) -> str:
        return "backup_manager"

    @property
    def description(self) -> str:
        return "管理数据库备份，支持创建、恢复、列出备份"

    @property
    def parameters(self) -> List[Dict]:
        return [
            {
                "name": "connection_id",
                "type": "string",
                "required": False,
                "description": "数据库连接 ID（可选）"
            },
            {
                "name": "action",
                "type": "string",
                "required": True,
                "enum": ["list", "create", "restore", "delete", "status"],
                "description": "操作类型"
            },
            {
                "name": "backup_name",
                "type": "string",
                "required": False,
                "description": "备份名称（create/restore/delete 时需要）"
            },
            {
                "name": "database",
                "type": "string",
                "required": False,
                "description": "数据库名（不填则使用配置的默认数据库）"
            }
        ]

    def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "")
        database = kwargs.get("database", self._get_default_database())

        if action == "list":
            return self._list_backups()
        elif action == "create":
            backup_name = kwargs.get("backup_name", f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            return self._create_backup(database, backup_name)
        elif action == "restore":
            backup_name = kwargs.get("backup_name", "")
            if not backup_name:
                return ToolResult(success=False, error="backup_name 不能为空")
            return self._restore_backup(database, backup_name)
        elif action == "delete":
            backup_name = kwargs.get("backup_name", "")
            if not backup_name:
                return ToolResult(success=False, error="backup_name 不能为空")
            return self._delete_backup(backup_name)
        elif action == "status":
            return self._backup_status()
        else:
            return ToolResult(success=False, error=f"Unknown action: {action}")

    def _get_default_database(self) -> str:
        """获取默认数据库"""
        config = get_config()
        monitor = config.get("monitor", {})
        db = config.get("database", {})
        return monitor.get("database", db.get("database", "erp_simulation"))

    def _ensure_backup_dir(self):
        """确保备份目录存在"""
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)

    def _list_backups(self) -> ToolResult:
        """列出所有备份"""
        try:
            self._ensure_backup_dir()

            backups = []
            for f in os.listdir(self.backup_dir):
                if f.endswith('.sql') or f.endswith('.dump') or f.endswith('.tar'):
                    filepath = os.path.join(self.backup_dir, f)
                    stat = os.stat(filepath)
                    backups.append({
                        "name": f,
                        "size": self._format_size(stat.st_size),
                        "size_bytes": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "path": filepath
                    })

            # 按时间排序
            backups.sort(key=lambda x: x["created_at"], reverse=True)

            return ToolResult(success=True, output={"backups": backups})
        except Exception as e:
            return ToolResult(success=False, error=f"列出备份失败: {str(e)}")

    def _create_backup(self, database: str, backup_name: str) -> ToolResult:
        """创建备份"""
        try:
            self._ensure_backup_dir()

            backup_file = os.path.join(self.backup_dir, f"{backup_name}.sql")
            pg_dump_cmd = [
                "pg_dump",
                "-Fc",  # 自定义格式压缩
                "-f", backup_file,
                "-d", database
            ]

            # 执行 pg_dump
            result = subprocess.run(
                pg_dump_cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return ToolResult(success=False, error=f"备份失败: {result.stderr}")

            # 获取备份文件大小
            size = os.path.getsize(backup_file)

            return ToolResult(
                success=True,
                output={
                    "name": f"{backup_name}.sql",
                    "size": self._format_size(size),
                    "size_bytes": size,
                    "database": database,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "path": backup_file
                }
            )
        except FileNotFoundError:
            return ToolResult(success=False, error="pg_dump 命令未找到，请确保 PostgreSQL 客户端已安装")
        except Exception as e:
            return ToolResult(success=False, error=f"创建备份失败: {str(e)}")

    def _restore_backup(self, database: str, backup_name: str) -> ToolResult:
        """恢复备份"""
        try:
            backup_file = os.path.join(self.backup_dir, backup_name)
            if not os.path.exists(backup_file):
                return ToolResult(success=False, error=f"备份文件不存在: {backup_name}")

            # 检查是否是 .sql 格式
            if backup_name.endswith('.sql'):
                # 使用 psql 恢复
                cmd = ["psql", "-d", database, "-f", backup_file]
            else:
                # 使用 pg_restore 恢复
                cmd = ["pg_restore", "-d", database, backup_file]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return ToolResult(success=False, error=f"恢复失败: {result.stderr}")

            return ToolResult(
                success=True,
                output={
                    "name": backup_name,
                    "database": database,
                    "restored_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "message": "备份恢复成功"
                }
            )
        except FileNotFoundError:
            return ToolResult(success=False, error="psql/pg_restore 命令未找到")
        except Exception as e:
            return ToolResult(success=False, error=f"恢复备份失败: {str(e)}")

    def _delete_backup(self, backup_name: str) -> ToolResult:
        """删除备份"""
        try:
            backup_file = os.path.join(self.backup_dir, backup_name)
            if not os.path.exists(backup_file):
                return ToolResult(success=False, error=f"备份文件不存在: {backup_name}")

            os.remove(backup_file)

            return ToolResult(
                success=True,
                output={
                    "name": backup_name,
                    "deleted": True,
                    "deleted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"删除备份失败: {str(e)}")

    def _backup_status(self) -> ToolResult:
        """获取备份状态"""
        try:
            self._ensure_backup_dir()

            total_size = 0
            backup_count = 0

            for f in os.listdir(self.backup_dir):
                if f.endswith('.sql') or f.endswith('.dump') or f.endswith('.tar'):
                    filepath = os.path.join(self.backup_dir, f)
                    total_size += os.path.getsize(filepath)
                    backup_count += 1

            # 检查 pg_dump 是否可用
            pg_dump_available = shutil.which("pg_dump") is not None

            return ToolResult(
                success=True,
                output={
                    "backup_dir": self.backup_dir,
                    "total_backups": backup_count,
                    "total_size": self._format_size(total_size),
                    "pg_dump_available": pg_dump_available
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"获取状态失败: {str(e)}")

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
