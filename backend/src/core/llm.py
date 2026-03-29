"""
LLM Client Module
使用 requests 调用 OpenAI 格式 API
Python 3.6.8 兼容
"""
import json
import requests
from typing import List, Dict, Generator
from .errors import LLMError


class LLMClient:
    """LLM 客户端，使用 requests 调用 OpenAI 格式 API"""

    def __init__(self, config: dict):
        self.base_url = config.get("base_url", "").rstrip("/")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.timeout = config.get("timeout", 120)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        """发送对话请求"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        endpoint = f"{self.base_url}/chat/completions"

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
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
        """流式发送对话请求"""
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
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.Timeout:
            raise LLMError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise LLMError(f"Request failed: {str(e)}")

    def chat_with_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0
    ) -> dict:
        """发送对话请求并期望返回 JSON"""
        response_text = self.chat(messages, temperature=temperature)
        json_str = self._extract_json(response_text)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                raise LLMError(f"Failed to parse JSON: {json_str}")
        raise LLMError(f"No valid JSON found in response: {response_text}")

    def _extract_json(self, text: str) -> str | None:
        """从文本中提取 JSON 字符串"""
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass

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
