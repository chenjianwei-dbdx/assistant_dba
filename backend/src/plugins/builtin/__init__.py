# Builtin plugins
from .query_executor import QueryExecutor
from .slow_query_analyzer import SlowQueryAnalyzer
from .index_analyzer import IndexAnalyzer
from .backup_manager import BackupManager
from .permission_manager import PermissionManager
from .connection_pool import ConnectionPoolMonitor

__all__ = [
    "QueryExecutor",
    "SlowQueryAnalyzer",
    "IndexAnalyzer",
    "BackupManager",
    "PermissionManager",
    "ConnectionPoolMonitor",
]


def register_all(registry):
    """注册所有内置插件到注册表"""
    registry.register(QueryExecutor())
    registry.register(SlowQueryAnalyzer())
    registry.register(IndexAnalyzer())
    registry.register(BackupManager())
    registry.register(PermissionManager())
    registry.register(ConnectionPoolMonitor())
