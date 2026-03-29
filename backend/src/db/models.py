"""
Database Models
数据库连接模型
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class DBConnection(Base):
    """数据库连接配置"""
    __tablename__ = "db_connections"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    db_type = Column(String(20), default="mysql")  # mysql, postgresql, sqlite
    host = Column(String(255))
    port = Column(Integer)
    database = Column(String(100))
    username = Column(String(100))
    password = Column(String(255))  # 应该加密存储
    charset = Column(String(20), default="utf8mb4")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "is_active": self.is_active
        }

    def get_connection_string(self) -> str:
        """获取连接字符串"""
        if self.db_type == "mysql":
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"
        elif self.db_type == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == "sqlite":
            return f"sqlite:///{self.database}"
        return ""


class QueryHistory(Base):
    """查询历史"""
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(36))
    sql = Column(Text, nullable=False)
    execution_time_ms = Column(Integer)
    row_count = Column(Integer)
    status = Column(String(20))  # success, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class VisitLog(Base):
    """访问日志"""
    __tablename__ = "visit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    page = Column(String(100), nullable=False)  # 页面路径
    user_id = Column(String(36), nullable=True)  # 用户ID（可选）
    ip_address = Column(String(50), nullable=True)  # IP地址
    user_agent = Column(String(255), nullable=True)  # 浏览器信息
    created_at = Column(DateTime, default=datetime.utcnow)
