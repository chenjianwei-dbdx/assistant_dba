"""
Dependency Injection Container - 统一管理所有依赖
"""
from functools import lru_cache
from typing import Optional
from .llm import LLMClient
from ..db.manager import ConnectionManager
from ..db.template_manager import TemplateManager


class Container:
    """统一 DI 容器"""

    def __init__(self):
        self._llm_client: Optional[LLMClient] = None
        self._connection_manager: Optional[ConnectionManager] = None
        self._template_manager: Optional[TemplateManager] = None
        self._plugin_registry = None

    def init(self, config: dict):
        """初始化所有依赖"""
        # LLM Client
        llm_config = config.get("llm", {})
        self._llm_client = LLMClient(llm_config)

        # Plugin Registry - 使用全局单例
        from ..plugins.registry import get_registry
        self._plugin_registry = get_registry()

        # 注册内置插件
        from ..plugins.builtin import register_all
        register_all(self._plugin_registry)

        # Connection Manager
        db_config = config.get("database", {})
        self._connection_manager = ConnectionManager(db_config)

        # Template Manager
        self._template_manager = TemplateManager()

    @property
    def llm_client(self) -> LLMClient:
        if self._llm_client is None:
            raise RuntimeError("Container not initialized")
        return self._llm_client

    @property
    def connection_manager(self) -> ConnectionManager:
        if self._connection_manager is None:
            raise RuntimeError("Container not initialized")
        return self._connection_manager

    @property
    def template_manager(self) -> TemplateManager:
        if self._template_manager is None:
            raise RuntimeError("Container not initialized")
        return self._template_manager

    @property
    def plugin_registry(self):
        return self._plugin_registry


# 全局容器
_container: Optional[Container] = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container


# FastAPI 依赖注入函数
@lru_cache()
def get_llm_client() -> LLMClient:
    return get_container().llm_client


@lru_cache()
def get_connection_manager() -> ConnectionManager:
    return get_container().connection_manager


@lru_cache()
def get_template_manager() -> TemplateManager:
    return get_container().template_manager


@lru_cache()
def get_plugin_registry():
    return get_container().plugin_registry


@lru_cache()
def get_plugin_context():
    """获取插件执行上下文"""
    from ..plugins.base import PluginContext
    return PluginContext(
        db_manager=get_connection_manager(),
        llm_client=get_llm_client(),
        config={}
    )
