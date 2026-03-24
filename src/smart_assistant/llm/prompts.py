"""
提示词管理模块
从 YAML 文件加载提示词模板
"""
import re
from pathlib import Path
from typing import Dict


class PromptManager:
    """提示词管理器"""

    def __init__(self, config_path: str = None):
        """
        初始化提示词管理器

        Args:
            config_path: 提示词配置文件路径
        """
        self.config_path = config_path or self._find_config_path()
        self.templates = self._load_templates()

    def _find_config_path(self) -> str:
        """查找配置文件"""
        current_dir = Path.cwd()
        config_path = current_dir / "configs" / "prompts.yaml"
        if config_path.exists():
            return str(config_path)

        module_dir = Path(__file__).parent.parent.parent
        config_path = module_dir / "configs" / "prompts.yaml"
        if config_path.exists():
            return str(config_path)

        raise FileNotFoundError("configs/prompts.yaml not found")

    def _load_templates(self) -> Dict:
        """加载模板"""
        import yaml
        with open(self.config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get("prompts", {})

    def get(self, name: str, **kwargs) -> str:
        """
        获取提示词模板

        Args:
            name: 模板名称
            **kwargs: 格式化参数

        Returns:
            格式化后的提示词
        """
        template = self.templates.get(name, "")
        if template and kwargs:
            # 使用安全的字符串替换方法
            return self._safe_format(template, **kwargs)
        return template

    def _safe_format(self, template: str, **kwargs) -> str:
        """
        安全的字符串格式化

        将 {{{{var}}}} 替换为 {var}（字面花括号）
        将 {var} 替换为对应的值
        """
        # 第一步：将 {{{{ 替换为 __LBRACE__，将 }}}} 替换为 __RBRACE__
        result = template.replace('{{{{', '__LBRACE__').replace('}}}}', '__RBRACE__')

        # 第二步：将单花括号 {var} 替换为对应值
        def replace_var(match):
            var_name = match.group(1)
            if var_name in kwargs:
                return str(kwargs[var_name])
            return match.group(0)  # 保留原样

        result = re.sub(r'\{(\w+)\}', replace_var, result)

        # 第三步：将 __LBRACE__ 和 __RBRACE__ 替换回花括号
        result = result.replace('__LBRACE__', '{').replace('__RBRACE__', '}')

        return result

    def intent_analysis(self, tool_definitions: str, user_input: str) -> str:
        """构建意图分析提示词"""
        return self.get(
            "intent_analysis",
            tool_definitions=tool_definitions,
            user_input=user_input
        )

    def param_extraction(
        self,
        task_description: str,
        tool_name: str,
        param_definitions: str,
        collected_params: Dict,
        missing_params: list,
        user_input: str
    ) -> str:
        """构建参数提取提示词"""
        return self.get(
            "param_extraction",
            task_description=task_description,
            tool_name=tool_name,
            param_definitions=param_definitions,
            collected_params=collected_params,
            missing_params=missing_params,
            user_input=user_input
        )

    def qa_response(self, conversation_history: str, user_input: str) -> str:
        """构建问答提示词"""
        return self.get(
            "qa_response",
            conversation_history=conversation_history,
            user_input=user_input
        )

    def tool_result_summary(
        self,
        tool_result: str,
        user_request: str,
        tool_name: str
    ) -> str:
        """构建工具结果总结提示词"""
        return self.get(
            "tool_result_summary",
            tool_result=tool_result,
            user_request=user_request,
            tool_name=tool_name
        )


# 全局实例
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """获取提示词管理器"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
