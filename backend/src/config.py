"""
Config Module
配置管理
"""
import os
from pathlib import Path


def load_config() -> dict:
    """加载配置"""
    config_path = Path(__file__).parent.parent.parent / "configs" / "settings.yaml"

    if not config_path.exists():
        return _default_config()

    import yaml
    with open(config_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 环境变量覆盖
    if os.environ.get("MINIMAX_API_KEY"):
        config["llm"]["api_key"] = os.environ["MINIMAX_API_KEY"]
    if os.environ.get("LLM_BASE_URL"):
        config["llm"]["base_url"] = os.environ["LLM_BASE_URL"]
    if os.environ.get("LLM_MODEL"):
        config["llm"]["model"] = os.environ["LLM_MODEL"]

    return config


def _default_config() -> dict:
    """默认配置"""
    return {
        "llm": {
            "provider": "minimax",
            "model": "MiniMax-M2",
            "api_key": os.environ.get("MINIMAX_API_KEY", ""),
            "base_url": "https://api.minimaxi.com/v1",
            "timeout": 120
        },
        "app": {
            "host": "0.0.0.0",
            "port": 8501
        }
    }


# 全局配置
_config = None


def get_config() -> dict:
    """获取配置"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
