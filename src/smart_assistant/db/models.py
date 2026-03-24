"""
数据库模型
使用 SQLAlchemy ORM，支持 SQLite 和 MySQL
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship, declarative_base
import hashlib

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def set_password(self, password: str):
        """设置密码（SHA256哈希）"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """验证密码"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Conversation(Base):
    """会话表"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, session_id={self.session_id})>"


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    tool_name = Column(String(64))
    tool_result = Column(Text)  # JSON 字符串
    intent_data = Column(Text)  # JSON 字符串
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_conversation_created", "conversation_id", "created_at"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role})>"


class ToolUsageLog(Base):
    """工具使用日志表"""
    __tablename__ = "tool_usage_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    tool_name = Column(String(64), nullable=False)
    params = Column(Text)  # JSON 字符串
    result = Column(Text)  # JSON 字符串
    success = Column(Boolean)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_tool_name", "tool_name"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<ToolUsageLog(id={self.id}, tool_name={self.tool_name})>"
