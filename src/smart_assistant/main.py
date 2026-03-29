"""
Smart Assistant - Streamlit 主入口
智能对话助手
"""
import streamlit as st
from pathlib import Path
import os
import sys
import json

# 添加 src 目录到路径，确保能找到 smart_assistant 模块
current_file = Path(__file__).resolve()
src_path = current_file.parent.parent  # src/
sys.path.insert(0, str(src_path))

# 确保工作目录正确
os.chdir(src_path.parent)  # 切换到项目根目录

from smart_assistant.config import get_config
from smart_assistant.db.database import get_db
from smart_assistant.db.models import Conversation, Message, User
from smart_assistant.llm.client import LLMClient
from smart_assistant.tools.registry import get_registry
from smart_assistant.tools.loader import load_tools_from_config
from smart_assistant.tools.sql_query import SQLQueryTool
from smart_assistant.db.schema_introspector import SchemaIntrospector
from smart_assistant.services.intent import IntentService
from smart_assistant.services.execution import ExecutionService
from smart_assistant.services.conversation import ConversationService


def hash_password(password: str) -> str:
    """密码哈希"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def init_services():
    """初始化服务"""
    # 加载配置
    config = get_config()

    # 初始化数据库
    db = get_db()

    # 初始化工具注册表
    tool_registry = get_registry()
    load_tools_from_config()

    # 初始化 LLM 客户端
    llm_config = config.llm
    llm_client = LLMClient(llm_config)

    # 初始化 SQL Query 工具（如果配置了 PostgreSQL）
    db_config = config.database
    if db_config.get("type") == "postgresql":
        try:
            schema_introspector = SchemaIntrospector(
                host=db_config.get("pg_host", "localhost"),
                port=db_config.get("pg_port", 5432),
                database=db_config.get("pg_database", "ai_intel"),
                username=db_config.get("pg_username", "postgres"),
                password=db_config.get("pg_password", "")
            )
            sql_query_tool = SQLQueryTool(llm_client, schema_introspector)
            tool_registry.register(sql_query_tool)
        except Exception as e:
            print(f"Warning: Failed to initialize SQL query tool: {e}")

    # 初始化服务
    intent_service = IntentService(llm_client, tool_registry)
    execution_service = ExecutionService(tool_registry)
    conversation_service = ConversationService(
        db, tool_registry, intent_service, execution_service
    )

    # 保存到 session_state
    st.session_state.conversation_service = conversation_service
    st.session_state.intent_service = intent_service
    st.session_state.tool_registry = tool_registry
    st.session_state.db = db


def load_conversation_messages(session_id: str, db) -> list:
    """从数据库加载会话消息"""
    session = db.get_session()
    try:
        # 查找会话
        conv = session.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()

        if not conv:
            return []

        # 加载消息
        messages = session.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at).all()

        result_list = []
        for msg in messages:
            tool_result = None
            if msg.tool_result:
                try:
                    tool_result = json.loads(msg.tool_result)
                except:
                    pass
            result_list.append({
                "role": msg.role,
                "content": msg.content,
                "tool_name": msg.tool_name,
                "success": tool_result.get("success") if tool_result else None
            })
        return result_list
    finally:
        session.close()


def get_all_conversations(db, user_id: int) -> list:
    """获取指定用户的所有会话列表"""
    session = db.get_session()
    try:
        convs = session.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_active == True
        ).order_by(Conversation.updated_at.desc()).limit(50).all()

        return [
            {
                "session_id": conv.session_id,
                "title": conv.title,
                "updated_at": conv.updated_at
            }
            for conv in convs
        ]
    finally:
        session.close()


def login_page():
    """登录/注册页面"""
    st.set_page_config(
        page_title="智能助手 - 登录",
        page_icon="🤖",
        layout="centered"
    )

    # 居中显示
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("")
        st.title("")
        st.title("🤖 智能助手")

        st.markdown("---")

        # Tab 选择：登录 / 注册
        tab1, tab2 = st.tabs(["🔑 登录", "📝 注册"])

        with tab1:
            st.markdown("### 登录已有账号")
            login_username = st.text_input("用户名", placeholder="请输入用户名...")
            login_password = st.text_input("密码", type="password", placeholder="请输入密码...")

            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                if st.button("登录", use_container_width=True, type="primary", key="login_btn"):
                    if login_username and login_password:
                        db = get_db()
                        session = db.get_session()
                        try:
                            user = session.query(User).filter(User.username == login_username).first()
                            if user and user.check_password(login_password):
                                # 登录成功
                                st.session_state.user_id = user.id
                                st.session_state.username = user.username
                                st.session_state.authenticated = True
                                st.query_params["user_id"] = str(user.id)
                                st.query_params["authenticated"] = "true"
                                st.rerun()
                            else:
                                st.error("❌ 用户名或密码错误")
                        finally:
                            session.close()
                    else:
                        st.warning("请输入用户名和密码")

        with tab2:
            st.markdown("### 注册新账号")
            reg_username = st.text_input("用户名", placeholder="请输入用户名...", key="reg_username")
            reg_password = st.text_input("密码", type="password", placeholder="请输入密码...", key="reg_password")
            reg_password2 = st.text_input("确认密码", type="password", placeholder="请再次输入密码...", key="reg_password2")
            reg_invite_code = st.text_input("邀请码", type="password", placeholder="请输入邀请码...", key="reg_invite_code")

            if st.button("注册", use_container_width=True, type="primary", key="register_btn"):
                if reg_username and reg_password and reg_invite_code:
                    # 验证邀请码
                    config = get_config()
                    correct_invite_code = config.app.get("invite_code", "VIP2024")
                    if reg_invite_code != correct_invite_code:
                        st.error("❌ 邀请码错误")
                    elif len(reg_username) < 3:
                        st.error("用户名至少3个字符")
                    elif len(reg_password) < 6:
                        st.error("密码至少6个字符")
                    elif reg_password != reg_password2:
                        st.error("两次密码不一致")
                    else:
                        db = get_db()
                        session = db.get_session()
                        try:
                            # 检查用户名是否已存在
                            existing = session.query(User).filter(User.username == reg_username).first()
                            if existing:
                                st.error("❌ 用户名已存在")
                            else:
                                # 创建新用户
                                user = User(
                                    username=reg_username,
                                    email=f"{reg_username}@smart-assistant.local"
                                )
                                user.set_password(reg_password)
                                session.add(user)
                                session.commit()

                                st.success("✅ 注册成功！请登录")
                                st.rerun()
                        finally:
                            session.close()
                else:
                    st.warning("请填写所有字段")

        st.markdown("---")
        st.markdown(
            "<p style='text-align: center; color: gray;'>"
            "首次使用请先注册账号"
            "</p>",
            unsafe_allow_html=True
        )


def load_conversation_messages(session_id: str, db) -> list:
    """从数据库加载会话消息"""
    session = db.get_session()
    try:
        conv = session.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()

        if not conv:
            return []

        messages = session.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at).all()

        result_list = []
        for msg in messages:
            tool_result = None
            if msg.tool_result:
                try:
                    tool_result = json.loads(msg.tool_result)
                except:
                    pass
            result_list.append({
                "role": msg.role,
                "content": msg.content,
                "tool_name": msg.tool_name,
                "success": tool_result.get("success") if tool_result else None
            })
        return result_list
    finally:
        session.close()


def get_all_conversations(db, user_id: int) -> list:
    """获取指定用户的所有会话列表"""
    session = db.get_session()
    try:
        convs = session.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_active == True
        ).order_by(Conversation.updated_at.desc()).limit(50).all()

        return [
            {
                "session_id": conv.session_id,
                "title": conv.title,
                "updated_at": conv.updated_at
            }
            for conv in convs
        ]
    finally:
        session.close()


def stream_response(prompt: str, intent_service: IntentService, conversation_service: ConversationService):
    """流式处理用户消息并产出响应"""
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    yield "🤔 正在分析您的意图...\n\n"

    intent_result = intent_service.analyze_intent(prompt)

    if intent_result["intent"] == "tool_use":
        tool_name = intent_result.get("tool_name")
        extracted_params = intent_result.get("extracted_params", {})
        missing_params = intent_result.get("missing_params", [])

        if missing_params:
            yield f"🔧 匹配到工具: `{tool_name}`\n\n"
            yield "📝 正在提取参数...\n\n"

            param_result = intent_service.extract_params(
                tool_name, extracted_params, missing_params, prompt
            )

            extracted = param_result.get("extracted", {})
            still_missing = param_result.get("still_missing", [])

            if still_missing:
                clarification = param_result.get("clarification_needed", "")
                yield f"📌 需要补充以下参数: {', '.join(still_missing)}\n\n"
                if clarification:
                    yield f"{clarification}\n\n"
            else:
                yield f"✅ 参数提取完成，准备执行工具 `{tool_name}`...\n\n"
                execution_service = ExecutionService(st.session_state.tool_registry)
                result = execution_service.execute(tool_name, extracted)

                if result["success"]:
                    yield f"✅ 工具执行成功!\n\n"
                    yield f"📤 输出:\n```\n{result.get('output', '')}\n```\n\n"
                else:
                    yield f"❌ 工具执行失败: {result.get('error', 'Unknown error')}\n\n"

        else:
            yield f"🔧 匹配到工具: `{tool_name}`\n\n"
            yield f"✅ 参数已提取，正在执行...\n\n"

            execution_service = ExecutionService(st.session_state.tool_registry)
            result = execution_service.execute(tool_name, extracted_params)

            if result["success"]:
                yield f"✅ 工具执行成功!\n\n"
                yield f"📤 输出:\n```\n{result.get('output', '')}\n```\n\n"
            else:
                yield f"❌ 工具执行失败: {result.get('error', 'Unknown error')}\n\n"

    elif intent_result["intent"] == "qa":
        yield "💬 正在思考回答...\n\n"
        messages = [{"role": "user", "content": prompt}]
        for chunk in intent_service.llm_client.chat_stream(messages, temperature=0.7):
            yield chunk
    else:
        yield "💬 正在思考回答...\n\n"
        messages = [{"role": "user", "content": prompt}]
        for chunk in intent_service.llm_client.chat_stream(messages, temperature=0.7):
            yield chunk


def main():
    """主函数"""
    query_params = st.query_params

    # 检查是否已登录
    if "authenticated" not in query_params or query_params.get("authenticated") != "true":
        login_page()
        return

    main_page()


def main_page():
    """主聊天页面"""
    st.set_page_config(
        page_title="智能助手",
        page_icon="🤖",
        layout="wide"
    )

    # 初始化服务
    init_services()

    # 初始化 session_state
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    query_params = st.query_params
    url_session_id = query_params.get("session_id")
    user_id = int(query_params.get("user_id", 0))

    # 侧边栏
    with st.sidebar:
        st.title(f"🤖 智能助手")
        st.caption(f"欢迎，{st.session_state.get('username', '用户')}")

        # 登出按钮
        if st.button("🚪 退出登录", use_container_width=True):
            query_params.clear()
            st.session_state.clear()
            st.rerun()

        st.divider()

        # 新对话按钮
        if st.button("➕ 新对话", use_container_width=True):
            query_params.clear()
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()

        st.divider()

        # 会话历史列表
        st.subheader("💬 我的会话")
        db = st.session_state.db
        conversations = get_all_conversations(db, user_id)

        if not conversations:
            st.caption("暂无历史会话")
        else:
            for conv in conversations:
                is_current = conv["session_id"] == st.session_state.get("session_id")
                button_type = "primary" if is_current else "secondary"

                if st.button(
                    f"📝 {conv['title'][:18]}..." if len(conv['title']) > 18 else f"📝 {conv['title']}",
                    key=f"conv_{conv['session_id']}",
                    use_container_width=True,
                    type=button_type
                ):
                    st.session_state.session_id = conv["session_id"]
                    st.session_state.messages = load_conversation_messages(conv["session_id"], db)
                    query_params["session_id"] = conv["session_id"]
                    st.rerun()

        st.divider()

        # 工具列表
        st.subheader("🛠️ 可用工具")
        tool_registry = st.session_state.tool_registry
        for tool in tool_registry.list_tools():
            with st.expander(f"📎 {tool.definition.name}"):
                st.caption(tool.definition.description)

    # 主聊天区域
    st.title("💬 对话")

    if url_session_id and st.session_state.get("session_id") != url_session_id:
        st.session_state.session_id = url_session_id
        st.session_state.messages = load_conversation_messages(url_session_id, db)

    for msg in st.session_state.messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        with st.chat_message(role):
            st.markdown(content)

            if msg.get("tool_name"):
                st.caption(f"🔧 工具: {msg['tool_name']}")

            if msg.get("success") is not None:
                if msg["success"]:
                    st.success("✅ 执行成功")
                else:
                    st.error("❌ 执行失败")

    if prompt := st.chat_input("输入消息..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        message_placeholder = st.empty()
        full_response = ""

        intent_service = st.session_state.intent_service
        conversation_service = st.session_state.conversation_service

        try:
            response_stream = stream_response(
                prompt,
                intent_service,
                conversation_service
            )

            for chunk in response_stream:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })

            if st.session_state.session_id is None:
                import uuid
                st.session_state.session_id = str(uuid.uuid4())

            # 保存到数据库
            session = db.get_session()
            try:
                # 获取或创建会话
                conv = session.query(Conversation).filter(
                    Conversation.session_id == st.session_state.session_id
                ).first()

                if not conv:
                    conv = Conversation(
                        session_id=st.session_state.session_id,
                        user_id=user_id,
                        title=prompt[:50]
                    )
                    session.add(conv)
                    session.commit()
                    session.refresh(conv)

                # 保存用户消息
                msg_user = Message(
                    conversation_id=conv.id,
                    role="user",
                    content=prompt
                )
                session.add(msg_user)

                # 保存助手消息
                msg_assistant = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=full_response
                )
                session.add(msg_assistant)

                session.commit()

            finally:
                session.close()

            query_params["session_id"] = st.session_state.session_id

        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })

        st.rerun()


if __name__ == "__main__":
    main()
