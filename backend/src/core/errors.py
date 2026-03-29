"""
DBA Assistant 错误类层次
统一的错误处理，所有业务异常都应使用此层次
"""
class DBAError(Exception):
    """基础错误类"""
    code: str = "DBA_ERROR"

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class LLMError(DBAError):
    """LLM 调用错误"""
    code = "LLM_ERROR"


class DatabaseError(DBAError):
    """数据库错误"""
    code = "DATABASE_ERROR"


class ToolExecutionError(DBAError):
    """工具执行错误"""
    code = "TOOL_ERROR"


class ValidationError(DBAError):
    """参数验证错误"""
    code = "VALIDATION_ERROR"