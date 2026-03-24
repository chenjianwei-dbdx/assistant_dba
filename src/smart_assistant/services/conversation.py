"""
对话服务模块
核心编排层，管理对话流程
"""
import uuid
import json
from enum import Enum
from typing import Dict, List, Optional, Any

from ..db.database import Database
from ..db.models import Conversation, Message
from ..tools.registry import ToolRegistry
from .intent import IntentService
from .execution import ExecutionService


class ConversationState(Enum):
    """对话状态"""
    IDLE = "idle"
    INTENT_PARSING = "intent_parsing"
    TOOL_MATCH = "tool_match"
    PARAM_EXTRACTION = "param_extraction"
    TOOL_EXECUTION = "tool_execution"
    QA_MODE = "qa_mode"
    RESPONDING = "responding"


class ConversationContext:
    """对话上下文"""

    def __init__(self):
        self.state = ConversationState.IDLE
        self.user_input = ""
        self.intent_result: Optional[Dict] = None
        self.collected_params: Dict = {}
        self.current_tool: Optional[str] = None
        self.pending_missing_params: List[str] = []
        self.messages: List[Dict] = []

    def reset(self):
        """重置上下文"""
        self.state = ConversationState.IDLE
        self.user_input = ""
        self.intent_result = None
        self.collected_params = {}
        self.current_tool = None
        self.pending_missing_params = []


class ConversationService:
    """对话服务 - 核心编排层"""

    def __init__(
        self,
        db: Database,
        tool_registry: ToolRegistry,
        intent_service: IntentService,
        execution_service: ExecutionService = None
    ):
        """
        初始化对话服务

        Args:
            db: 数据库实例
            tool_registry: 工具注册表
            intent_service: 意图服务
            execution_service: 执行服务
        """
        self.db = db
        self.tool_registry = tool_registry
        self.intent_service = intent_service
        self.execution_service = execution_service or ExecutionService(tool_registry)
        self._contexts: Dict[str, ConversationContext] = {}

    def process_message(
        self,
        user_input: str,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        处理用户消息

        Args:
            user_input: 用户输入
            session_id: 会话 ID

        Returns:
            处理结果:
            {
                "content": str,           # 回复内容
                "tool_name": str,          # 工具名称（如果有）
                "needs_params": list,      # 需要的参数（如果需要更多输入）
                "state": str               # 当前状态
            }
        """
        # 获取或创建会话
        session_id, conversation = self._get_or_create_session(session_id)

        # 获取上下文
        context = self._get_context(session_id)

        # 判断是否在参数提取状态
        if context.state == ConversationState.PARAM_EXTRACTION:
            return self._handle_param_extraction(
                user_input, session_id, conversation, context
            )

        # 保存用户消息
        self._save_message(
            conversation.id,
            "user",
            user_input
        )

        # 意图分析
        intent_result = self.intent_service.analyze_intent(user_input)
        context.intent_result = intent_result
        context.user_input = user_input

        # 路由处理
        if intent_result["intent"] == "tool_use":
            return self._handle_tool_use(
                intent_result, user_input, session_id, conversation, context
            )
        elif intent_result["intent"] == "qa":
            return self._handle_qa(
                user_input, session_id, conversation, context
            )
        else:
            # 未知意图，当作 QA 处理
            return self._handle_qa(
                user_input, session_id, conversation, context
            )

    def _handle_tool_use(
        self,
        intent_result: Dict,
        user_input: str,
        session_id: str,
        conversation,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """处理工具使用"""
        tool_name = intent_result.get("tool_name")
        extracted_params = intent_result.get("extracted_params", {})
        missing_params = intent_result.get("missing_params", [])

        # 检查工具是否存在
        if not self.execution_service.validate_tool_exists(tool_name):
            return {
                "content": f"抱歉，暂不支持该工具: {tool_name}",
                "state": "error"
            }

        # 更新已收集的参数
        context.collected_params.update(extracted_params)
        context.current_tool = tool_name

        # 检查是否需要更多参数
        if missing_params:
            context.state = ConversationState.PARAM_EXTRACTION
            context.pending_missing_params = missing_params

            # 生成参数询问
            clarification = self._generate_param_clarification(
                tool_name, missing_params
            )

            return {
                "content": clarification,
                "needs_params": missing_params,
                "state": "param_extraction"
            }

        # 参数齐全，执行工具
        return self._execute_tool(
            tool_name,
            context.collected_params,
            user_input,
            session_id,
            conversation
        )

    def _handle_param_extraction(
        self,
        user_input: str,
        session_id: str,
        conversation,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """处理参数提取"""
        tool_name = context.current_tool
        missing_params = context.pending_missing_params
        collected = context.collected_params

        # 调用 LLM 提取参数
        result = self.intent_service.extract_params(
            tool_name,
            collected,
            missing_params,
            user_input
        )

        # 更新已收集的参数
        context.collected_params.update(result.get("extracted", {}))

        # 检查是否还有缺失参数
        still_missing = result.get("still_missing", [])
        if still_missing:
            context.pending_missing_params = still_missing
            clarification = result.get("clarification_needed", "")
            if not clarification:
                clarification = self._generate_param_clarification(
                    tool_name, still_missing
                )
            return {
                "content": clarification,
                "needs_params": still_missing,
                "state": "param_extraction"
            }

        # 参数齐全，执行工具
        context.state = ConversationState.IDLE
        context.pending_missing_params = []

        return self._execute_tool(
            tool_name,
            context.collected_params,
            context.user_input,
            session_id,
            conversation
        )

    def _execute_tool(
        self,
        tool_name: str,
        params: Dict,
        user_request: str,
        session_id: str,
        conversation
    ) -> Dict[str, Any]:
        """执行工具"""
        context = self._get_context(session_id)
        context.state = ConversationState.TOOL_EXECUTION

        # 执行工具
        result = self.execution_service.execute(tool_name, params)

        # 保存工具执行结果
        self._save_message(
            conversation.id,
            "tool",
            json.dumps(result, ensure_ascii=False),
            tool_name=tool_name,
            tool_result=result
        )

        # 生成自然语言响应
        if result["success"]:
            response = self.intent_service.summarize_tool_result(
                result,
                user_request,
                tool_name
            )
        else:
            response = f"工具执行失败: {result.get('error', 'Unknown error')}"

        # 保存助手回复
        self._save_message(
            conversation.id,
            "assistant",
            response,
            tool_name=tool_name,
            tool_result=result
        )

        # 重置上下文
        context.reset()

        return {
            "content": response,
            "tool_name": tool_name,
            "success": result["success"],
            "state": "completed"
        }

    def _handle_qa(
        self,
        user_input: str,
        session_id: str,
        conversation,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """处理问答模式"""
        context.state = ConversationState.QA_MODE

        # 获取对话历史
        history = self._get_conversation_history(conversation.id)

        # 生成回复
        response = self.intent_service.generate_qa_response(history, user_input)

        # 保存助手回复
        self._save_message(
            conversation.id,
            "assistant",
            response
        )

        # 重置上下文
        context.reset()

        return {
            "content": response,
            "state": "qa_mode"
        }

    def _generate_param_clarification(
        self,
        tool_name: str,
        missing_params: List[str]
    ) -> str:
        """生成参数询问"""
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return f"请提供以下参数: {', '.join(missing_params)}"

        schema = tool.definition.get_param_schema()
        lines = ["我需要一些参数来完成这个操作："]

        for param_name in missing_params:
            if param_name in schema:
                param = schema[param_name]
                description = param.get("description", "")
                enum = param.get("enum")
                default = param.get("default")

                line = f"- **{param_name}**: {description}"
                if enum:
                    line += f"（可选值: {', '.join(enum)}）"
                if default is not None:
                    line += f"，默认: {default}"
                lines.append(line)

        return "\n".join(lines)

    def _get_or_create_session(self, session_id: str = None):
        """获取或创建会话"""
        if session_id is None:
            session_id = str(uuid.uuid4())

        session = self.db.get_session()
        try:
            # 查找现有会话
            conv = session.query(Conversation).filter(
                Conversation.session_id == session_id
            ).first()

            if not conv:
                # 创建新会话
                conv = Conversation(
                    session_id=session_id,
                    title="新对话"
                )
                session.add(conv)
                session.commit()
                session.refresh(conv)

            return session_id, conv
        finally:
            session.close()

    def _get_context(self, session_id: str) -> ConversationContext:
        """获取会话上下文"""
        if session_id not in self._contexts:
            self._contexts[session_id] = ConversationContext()
        return self._contexts[session_id]

    def _save_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        tool_name: str = None,
        tool_result: Dict = None,
        intent_data: Dict = None
    ) -> None:
        """保存消息"""
        session = self.db.get_session()
        try:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                tool_name=tool_name,
                tool_result=json.dumps(tool_result, ensure_ascii=False) if tool_result else None,
                intent_data=json.dumps(intent_data, ensure_ascii=False) if intent_data else None
            )
            session.add(message)

            # 更新会话标题（如果是第一条用户消息）
            if role == "user":
                conv = session.query(Conversation).get(conversation_id)
                if conv and conv.title == "新对话" and len(content) > 0:
                    conv.title = content[:50]

            session.commit()
        finally:
            session.close()

    def _get_conversation_history(
        self,
        conversation_id: int,
        limit: int = 20
    ) -> List[Dict]:
        """获取对话历史"""
        session = self.db.get_session()
        try:
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(limit).all()

            # 反转，按时间正序
            messages = list(reversed(messages))

            return [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in messages
            ]
        finally:
            session.close()

    def new_session(self) -> str:
        """创建新会话，返回 session_id"""
        session_id = str(uuid.uuid4())
        self._get_context(session_id)  # 初始化上下文
        return session_id
