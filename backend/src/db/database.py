"""
统一的数据库连接管理
所有数据库连接均通过此类获取，消除 psycopg2/SQLAlchemy 调用碎片化
"""
import psycopg2
from typing import Optional
from contextlib import contextmanager


class DatabaseManager:
    """统一的数据库连接管理器"""

    def __init__(self, config: dict):
        self.config = config

    def _build_dsn(self) -> dict:
        host = self.config.get("host", "127.0.0.1")
        port = self.config.get("port", 5432)
        user = self.config.get("username", "cjwdsg")
        password = self.config.get("password", "")
        database = self.config.get("database", "erp_simulation")
        return {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }

    @contextmanager
    def get_psycopg2_connection(self):
        """获取 psycopg2 连接（用于原生 SQL 执行）"""
        dsn = self._build_dsn()
        conn = psycopg2.connect(**dsn)
        try:
            yield conn
        finally:
            conn.close()

    def get_connection_info(self) -> dict:
        """获取当前连接信息（用于调试）"""
        return self._build_dsn()


# 全局实例（由 Container 管理，此处仅作为便捷回退）
_default_manager: Optional[DatabaseManager] = None


def get_default_manager() -> DatabaseManager:
    global _default_manager
    if _default_manager is None:
        from src.config import get_config
        _default_manager = DatabaseManager(get_config().get("database", {}))
    return _default_manager