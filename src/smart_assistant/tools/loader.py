"""
工具加载器模块
从 YAML 配置加载工具定义
"""
import subprocess
import os
from pathlib import Path
from typing import Dict, Any
import yaml

from .base import ToolDefinition
from .registry import get_registry, ToolRegistry


class ScriptTool:
    """脚本执行器"""

    def __init__(self, script_path: str, timeout: int = 30):
        self.script_path = script_path
        self.timeout = timeout

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行脚本

        Args:
            **kwargs: 脚本参数，会转换为命令行参数

        Returns:
            执行结果
        """
        # 解析脚本路径
        script_full_path = self._resolve_script_path()

        if not os.path.exists(script_full_path):
            return {
                "success": False,
                "error": f"Script not found: {script_full_path}"
            }

        # 构建命令
        cmd = [script_full_path]
        for key, value in kwargs.items():
            if value is not None:
                cmd.extend([f"--{key}", str(value)])

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout
            )
            stdout = result.stdout.decode("utf-8", errors="replace")
            stderr = result.stderr.decode("utf-8", errors="replace")
            return {
                "success": result.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Script execution timeout ({self.timeout}s)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Script execution failed: {str(e)}"
            }

    def _resolve_script_path(self) -> str:
        """解析脚本路径"""
        if os.path.isabs(self.script_path):
            return self.script_path

        # 相对于项目根目录
        project_root = Path(__file__).parent.parent.parent.parent
        return str(project_root / self.script_path)


def load_tools_from_config(config_path: str = None, registry: ToolRegistry = None) -> None:
    """
    从 YAML 配置加载工具

    Args:
        config_path: 配置文件路径
        registry: 工具注册表，如果为 None 则使用全局注册表
    """
    if registry is None:
        registry = get_registry()

    if config_path is None:
        config_path = _find_tools_config()

    if not config_path or not os.path.exists(config_path):
        return

    with open(config_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)

    tools_config = config.get("tools", [])

    for tool_config in tools_config:
        _load_single_tool(tool_config, registry)


def _load_single_tool(tool_config: Dict, registry: ToolRegistry) -> None:
    """加载单个工具"""
    name = tool_config["name"]
    description = tool_config["description"]
    category = tool_config.get("category", "general")
    parameters = tool_config.get("parameters", [])
    script_path = tool_config.get("script_path")
    timeout = tool_config.get("timeout", 30)

    # 创建工具定义
    definition = ToolDefinition(
        name=name,
        description=description,
        category=category,
        parameters=parameters,
        script_path=script_path,
        timeout=timeout
    )

    # 创建脚本执行器
    if script_path:
        script_tool = ScriptToolRunner(definition)
        registry.register(script_tool)


class ScriptToolRunner:
    """脚本工具运行器"""

    def __init__(self, definition: ToolDefinition):
        self.definition = definition
        self._runner = ScriptTool(definition.script_path, definition.timeout)

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行脚本工具"""
        return self._runner.execute(**kwargs)

    def validate_params(self, **kwargs) -> tuple:
        """
        验证参数

        Returns:
            (is_valid, missing_params, invalid_params)
        """
        definition = self.definition
        required = definition.get_required_params()
        schema = definition.get_param_schema()

        missing = []
        invalid = {}

        for param_name in required:
            if param_name not in kwargs or kwargs[param_name] is None:
                missing.append(param_name)

        for param_name, value in kwargs.items():
            if param_name in schema:
                param_schema = schema[param_name]
                if param_schema.get("enum") and value not in param_schema["enum"]:
                    invalid[param_name] = f"Value must be one of {param_schema['enum']}"

        return len(missing) == 0 and len(invalid) == 0, missing, invalid


def _find_tools_config() -> str:
    """查找工具配置文件"""
    # 优先查找当前目录
    current_dir = Path.cwd()
    config_path = current_dir / "configs" / "tools.yaml"
    if config_path.exists():
        return str(config_path)

    # 查找模块目录
    module_dir = Path(__file__).parent.parent.parent
    config_path = module_dir / "configs" / "tools.yaml"
    if config_path.exists():
        return str(config_path)

    return None


def register_builtin_tools(registry: ToolRegistry = None) -> None:
    """
    注册内置工具

    Args:
        registry: 工具注册表
    """
    if registry is None:
        registry = get_registry()

    # 这里可以添加内置的 Python 工具
    # 例如：registry.register(MyBuiltinTool())
    pass
