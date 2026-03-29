"""
FastAPI 依赖注入容器
统一提供 LLMClient、ConnectionManager、TemplateManager、PluginRegistry
"""
from functools import lru_cache
from typing import Optional
from .llm import LLMClient
from ..db.manager import ConnectionManager
from ..db.template_manager import TemplateManager
from ..plugins.registry import PluginRegistry


class Container:
    """依赖注入容器"""
    _llm_client: Optional[LLMClient] = None
    _connection_manager: Optional[ConnectionManager] = None
    _template_manager: Optional[TemplateManager] = None
    _registry: Optional[PluginRegistry] = None

    def init(self, config: dict):
        self._llm_client = LLMClient(config.get("llm", {}))
        db_config = config.get("database", {})
        self._connection_manager = ConnectionManager(db_config)
        self._template_manager = TemplateManager()
        self._registry = PluginRegistry()
        # 注册插件
        from ..plugins.builtin import register_all
        register_all(self._registry)

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
    def registry(self) -> PluginRegistry:
        if self._registry is None:
            raise RuntimeError("Container not initialized")
        return self._registry


_container = Container()


def get_container() -> Container:
    return _container


@lru_cache
def get_llm_client() -> LLMClient:
    return _container.llm_client


def get_connection_manager() -> ConnectionManager:
    return _container.connection_manager


def get_template_manager() -> TemplateManager:
    return _container.template_manager


def get_registry() -> PluginRegistry:
    return _container.registry
