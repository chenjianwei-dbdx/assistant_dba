"""
数据库连接模块
支持 SQLite、MySQL 和 PostgreSQL，通过配置切换
"""
import os
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base


class Database:
    """数据库连接管理器"""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._engine is None:
            self._init_engine()

    def _init_engine(self):
        """初始化数据库引擎"""
        from ..config import get_config
        config = get_config()
        db_config = config.database

        db_type = db_config.get("type", "sqlite")

        if db_type == "sqlite":
            self._init_sqlite(db_config)
        elif db_type == "mysql":
            self._init_mysql(db_config)
        elif db_type == "postgresql":
            self._init_postgresql(db_config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        # 创建表
        Base.metadata.create_all(self._engine)

    def _init_sqlite(self, db_config: dict):
        """初始化 SQLite"""
        db_path = db_config.get("db_path", "data/smart_assistant.db")

        # 确保目录存在
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # SQLite 连接 URL
        db_url = f"sqlite:///{db_path}"

        self._engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )

    def _init_mysql(self, db_config: dict):
        """初始化 MySQL"""
        host = db_config.get("host", "localhost")
        port = db_config.get("port", 3306)
        username = db_config.get("username", "root")
        password = db_config.get("password", "")
        database = db_config.get("database", "smart_assistant")
        charset = db_config.get("charset", "utf8mb4")

        db_url = (
            f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
            f"?charset={charset}"
        )

        self._engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )

    def _init_postgresql(self, db_config: dict):
        """初始化 PostgreSQL"""
        host = db_config.get("host", "localhost")
        port = db_config.get("port", 5432)
        username = db_config.get("username", "cjwdsg")
        password = db_config.get("password", "")
        database = db_config.get("database", "smart_assistant")

        db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"

        self._engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )

    def get_session(self) -> Session:
        """获取数据库会话"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self._engine)
        return self._session_factory()

    def close(self):
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


def get_db() -> Database:
    """获取数据库单例"""
    return Database()
