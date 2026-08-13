import json
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.integrations.base_llm import BaseLLMProvider


class OpenAIService(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "openai"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_message(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        api_key = settings.LLM_KEY or getattr(settings, "OPENAI_API_KEY", None)
        if not api_key:
            raise ValueError("OpenAI API Key is not configured. Please set LLM_KEY or OPENAI_API_KEY.")

        model = settings.LLM_MODEL if settings.LLM_MODEL else "gpt-4o-mini"
        logger.info(f"Generating message using OpenAI provider with model {model}")

        openai_tools = []
        if tools:
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"]
                    }
                })

        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "tool":
                formatted_messages.append({
                    "role": "tool",
                    "content": content,
                    "tool_call_id": msg.get("tool_call_id", "mock_id")
                })
            elif role == "assistant" and msg.get("tool_calls"):
                tc_list = []
                for tc in msg["tool_calls"]:
                    tc_list.append({
                        "id": tc.get("id") or "mock_id",
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["args"])
                        }
                    })
                formatted_messages.append({
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tc_list
                })
            else:
                formatted_messages.append({
                    "role": role,
                    "content": content
                })

        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        if openai_tools:
            payload["tools"] = openai_tools

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        url = "https://api.openai.com/v1/chat/completions"
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"OpenAI returned error status {response.status_code}: {response.text}")
                raise Exception(f"OpenAI error: {response.text}")

            data = response.json()
            choice = data["choices"][0]
            msg = choice["message"]
            content_text = msg.get("content") or ""
            tool_calls = []

            raw_tool_calls = msg.get("tool_calls") or []
            for tc in raw_tool_calls:
                fn = tc["function"]
                tc_args = fn.get("arguments") or "{}"
                if isinstance(tc_args, str):
                    try:
                        parsed_args = json.loads(tc_args)
                    except Exception:
                        parsed_args = {}
                else:
                    parsed_args = tc_args

                tool_calls.append({
                    "id": tc.get("id") or "call_id",
                    "name": fn["name"],
                    "args": parsed_args
                })

            usage = data.get("usage", {})
            return {
                "content": content_text,
                "tool_calls": tool_calls,
                "usage": {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0)
                }
            }
        except Exception as e:
            logger.exception("OpenAI API call failed")
            raise e


openai_service = OpenAIService()
