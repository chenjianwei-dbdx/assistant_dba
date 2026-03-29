"""
Database Connection Utility
提供共享的数据库连接
"""
from .database import get_default_manager


def get_monitor_connection():
    """获取监控数据库连接（用于性能监控和 AI 分析）"""
    return get_default_manager().get_psycopg2_connection().__enter__()