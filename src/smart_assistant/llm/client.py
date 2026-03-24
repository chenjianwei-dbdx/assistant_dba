"""
LLM 客户端模块
使用 requests 调用 OpenAI 格式 API，兼容 MiniMax、Ollama 等
Python 3.6.8 兼容，不使用 openai SDK
"""
import json
import requests
from typing import List, Dict, Optional, Generator


class LLMClient:
    """LLM 客户端，使用 requests 调用 OpenAI 格式 API"""

    def __init__(self, config: dict):
        """
        初始化 LLM 客户端

        Args:
            config: LLM 配置，应包含 base_url, api_key, model, timeout
        """
        self.base_url = config.get("base_url", "").rstrip("/")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.timeout = config.get("timeout", 120)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """
        发送对话请求

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            stream: 是否流式响应

        Returns:
            模型生成的回复内容
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        if stream:
            payload["stream"] = True

        endpoint = f"{self.base_url}/chat/completions"

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()

            if stream:
                return self._handle_stream_response(response)
            else:
                result = response.json()
                return result["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout:
            raise LLMError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise LLMError(f"Request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise LLMError(f"Invalid response format: {str(e)}")

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        流式发送对话请求，逐字产出

        Args:
            messages: 消息列表
            temperature: 温度参数

        Yields:
            生成的文本片段
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }

        endpoint = f"{self.base_url}/chat/completions"

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line_text = line.decode("utf-8")
                    if line_text.startswith("data: "):
                        data = line_text[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    content = delta["content"]
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.Timeout:
            raise LLMError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise LLMError(f"Request failed: {str(e)}")

    def _handle_stream_response(self, response) -> str:
        """处理流式响应"""
        full_content = []
        for line in response.iter_lines():
            if line:
                line_text = line.decode("utf-8")
                if line_text.startswith("data: "):
                    data = line_text[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if "choices" in chunk:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                full_content.append(delta["content"])
                    except json.JSONDecodeError:
                        continue
        return "".join(full_content)

    def chat_with_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0
    ) -> dict:
        """
        发送对话请求并期望返回 JSON

        Args:
            messages: 消息列表
            temperature: 温度参数（建议用 0 以获得更稳定的 JSON 输出）

        Returns:
            解析后的 JSON 对象
        """
        response_text = self.chat(messages, temperature=temperature)

        # 尝试提取 JSON
        json_str = self._extract_json(response_text)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                raise LLMError(f"Failed to parse JSON: {json_str}")

        raise LLMError(f"No valid JSON found in response: {response_text}")

    def _extract_json(self, text: str) -> Optional[str]:
        """从文本中提取 JSON 字符串"""
        # 尝试直接解析
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass

        # 尝试查找 JSON 代码块
        import re
        patterns = [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
            r"\{[\s\S]*\}"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1) if "```" in pattern else match.group(0)
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    continue

        return None


class LLMError(Exception):
    """LLM 调用错误"""
    pass


def create_llm_client(config: dict) -> LLMClient:
    """工厂函数，创建 LLM 客户端"""
    return LLMClient(config)
