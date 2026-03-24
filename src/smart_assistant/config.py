"""
配置管理模块
所有配置从 YAML 文件加载，不硬编码
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict


class Config:
    """配置类，加载并管理所有配置"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self):
        """从 YAML 文件加载配置"""
        config_path = self._find_config_path()
        with open(config_path, encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        # 支持环境变量覆盖
        self._apply_env_overrides()

    def _find_config_path(self) -> Path:
        """查找配置文件路径"""
        # 优先查找当前目录
        current_dir = Path.cwd()
        config_path = current_dir / "configs" / "settings.yaml"
        if config_path.exists():
            return config_path

        # 查找模块目录
        module_dir = Path(__file__).parent.parent.parent
        config_path = module_dir / "configs" / "settings.yaml"
        if config_path.exists():
            return config_path

        raise FileNotFoundError("configs/settings.yaml not found")

    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        # LLM API Key
        if os.environ.get("MINIMAX_API_KEY"):
            self._config["llm"]["api_key"] = os.environ["MINIMAX_API_KEY"]

        # 数据库密码
        if os.environ.get("DB_PASSWORD"):
            self._config["database"]["password"] = os.environ["DB_PASSWORD"]

        # Ollama 配置
        if os.environ.get("OLLAMA_BASE_URL"):
            self._config["llm"]["base_url"] = os.environ["OLLAMA_BASE_URL"]
        if os.environ.get("OLLAMA_MODEL"):
            self._config["llm"]["model"] = os.environ["OLLAMA_MODEL"]

    def get(self, *keys: str, default: Any = None) -> Any:
        """获取配置值，支持嵌套 key"""
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value

    @property
    def llm(self) -> Dict:
        """获取 LLM 配置"""
        return self._config.get("llm", {})

    @property
    def database(self) -> Dict:
        """获取数据库配置"""
        return self._config.get("database", {})

    @property
    def app(self) -> Dict:
        """获取应用配置"""
        return self._config.get("app", {})

    def reload(self):
        """重新加载配置"""
        self._config = None
        self._load_config()


def get_config() -> Config:
    """获取配置单例"""
    return Config()
