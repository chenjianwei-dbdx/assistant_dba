"""
Database Manager
数据库连接管理器
"""
import uuid
from typing import Optional, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import DBConnection, Base


class ConnectionManager:
    """连接管理器"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.db_type = self.config.get("type", "sqlite")
        self.engine = None
        self.SessionLocal = None
        self._init_db()
        # 初始化默认 PostgreSQL 连接
        self._init_default_connection()

    def _init_default_connection(self):
        """初始化默认 PostgreSQL 连接（如果不存在）"""
        session = self.get_session()
        try:
            # 检查是否已存在 erp_simulation 连接
            existing = session.query(DBConnection).filter_by(name="ERP仿真数据库").first()
            if not existing:
                # 创建默认连接
                default_conn = DBConnection(
                    id=str(uuid.uuid4()),
                    name="ERP仿真数据库",
                    db_type="postgresql",
                    host="127.0.0.1",
                    port=5432,
                    database="erp_simulation",
                    username="cjwdsg",
                    password="",
                    charset="utf8"
                )
                session.add(default_conn)
                session.commit()
        finally:
            session.close()

    def _init_db(self):
        """初始化数据库"""
        if self.db_type == "postgresql":
            # PostgreSQL 连接
            self.engine = create_engine(
                f"postgresql://{self.config.get('username', 'sa_admin')}:{self.config.get('password', '')}@{self.config.get('host', 'localhost')}:{self.config.get('port', 5432)}/{self.config.get('database', 'smart_assistant')}"
            )
        elif self.db_type == "mysql":
            # MySQL 连接
            self.engine = create_engine(
                f"mysql+pymysql://{self.config.get('username', 'root')}:{self.config.get('password', '')}@{self.config.get('host', 'localhost')}:{self.config.get('port', 3306)}/{self.config.get('database', 'smart_assistant')}?charset={self.config.get('charset', 'utf8mb4')}"
            )
        else:
            # SQLite 默认
            db_path = self.config.get("db_path", "data/connections.db")
            import os
            os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
            self.engine = create_engine(f"sqlite:///{db_path}")

        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """获取会话"""
        return self.SessionLocal()

    def create_connection(self, data: Dict) -> DBConnection:
        """创建连接"""
        session = self.get_session()
        try:
            conn = DBConnection(
                id=str(uuid.uuid4()),
                name=data["name"],
                db_type=data.get("db_type", "mysql"),
                host=data.get("host", "localhost"),
                port=data.get("port", 3306),
                database=data.get("database", ""),
                username=data.get("username", ""),
                password=data.get("password", ""),
                charset=data.get("charset", "utf8mb4")
            )
            session.add(conn)
            session.commit()
            session.refresh(conn)
            return conn
        finally:
            session.close()

    def list_connections(self) -> list:
        """列出所有连接"""
        session = self.get_session()
        try:
            return [c.to_dict() for c in session.query(DBConnection).all()]
        finally:
            session.close()

    def get_connection(self, conn_id: str) -> Optional[DBConnection]:
        """获取连接"""
        session = self.get_session()
        try:
            return session.query(DBConnection).filter_by(id=conn_id).first()
        finally:
            session.close()

    def delete_connection(self, conn_id: str) -> bool:
        """删除连接"""
        session = self.get_session()
        try:
            conn = session.query(DBConnection).filter_by(id=conn_id).first()
            if conn:
                session.delete(conn)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def test_connection(self, data: Dict) -> Dict:
        """测试连接"""
        try:
            db_type = data.get("db_type", "mysql")
            if db_type == "mysql":
                engine = create_engine(
                    f"mysql+pymysql://{data['username']}:{data['password']}@{data['host']}:{data['port']}/{data['database']}?charset={data.get('charset', 'utf8mb4')}"
                )
            elif db_type == "postgresql":
                engine = create_engine(
                    f"postgresql://{data['username']}:{data['password']}@{data['host']}:{data['port']}/{data['database']}"
                )
            else:
                return {"success": False, "error": f"Unsupported database type: {db_type}"}

            # 测试连接
            conn = engine.connect()
            conn.close()
            return {"success": True, "message": "Connection successful"}

        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局实例
_manager: Optional[ConnectionManager] = None


def get_connection_manager(config: dict = None) -> ConnectionManager:
    """获取连接管理器"""
    global _manager
    if _manager is None:
        _manager = ConnectionManager(config)
    return _manager
