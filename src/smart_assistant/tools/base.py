"""
工具基类模块
所有工具必须继承 BaseTool 并实现抽象方法
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class ToolDefinition:
    """工具定义数据类"""

    def __init__(
        self,
        name: str,
        description: str,
        category: str = "general",
        parameters: List[Dict] = None,
        script_path: str = None,
        timeout: int = 30,
        handler: Any = None
    ):
        self.name = name
        self.description = description
        self.category = category
        self.parameters = parameters or []
        self.script_path = script_path
        self.timeout = timeout
        self.handler = handler

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "script_path": self.script_path,
            "timeout": self.timeout
        }

    def get_required_params(self) -> List[str]:
        """获取必填参数列表"""
        return [p["name"] for p in self.parameters if p.get("required", False)]

    def get_param_schema(self) -> Dict[str, Dict]:
        """获取参数 schema"""
        schema = {}
        for p in self.parameters:
            schema[p["name"]] = {
                "type": p.get("type", "string"),
                "description": p.get("description", ""),
                "required": p.get("required", False),
                "enum": p.get("enum"),
                "default": p.get("default")
            }
        return schema


class BaseTool(ABC):
    """工具基类，所有工具必须继承此类"""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """返回工具定义"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果字典，应包含:
            - success: bool 是否成功
            - output: str 输出内容
            - error: str 错误信息（如果失败）
        """
        pass

    def validate_params(self, **kwargs) -> tuple:
        """
        验证参数

        Returns:
            (is_valid, missing_params, error_params)
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
                # 检查枚举值
                if param_schema.get("enum") and value not in param_schema["enum"]:
                    invalid[param_name] = f"Value must be one of {param_schema['enum']}"

        return len(missing) == 0 and len(invalid) == 0, missing, invalid
