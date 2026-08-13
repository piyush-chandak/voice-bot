import json
from typing import Any, Dict, List, Optional
from anthropic import AsyncAnthropic
from app.core.config import settings
from app.core.logging import logger
from app.integrations.base_llm import BaseLLMProvider


class AnthropicService(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "anthropic"

    def __init__(self):
        self._client: Optional[AsyncAnthropic] = None

    @property
    def client(self) -> AsyncAnthropic:
        if not self._client:
            api_key = settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError("Anthropic API key is not configured. Please set ANTHROPIC_API_KEY.")
            self._client = AsyncAnthropic(api_key=api_key)
        return self._client

    async def generate_message(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        api_key_set = settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.strip()
        if not api_key_set:
            raise ValueError("Anthropic API key is not configured. Please set ANTHROPIC_API_KEY.")

        try:
            # Map tools to Anthropic tool schema format if provided
            anthropic_tools = []
            if tools:
                for tool in tools:
                    anthropic_tools.append({
                        "name": tool["name"],
                        "description": tool["description"],
                        "input_schema": tool["input_schema"]
                    })

            kwargs = {
                "model": settings.LLM_MODEL if settings.LLM_MODEL.startswith("claude") else "claude-3-5-sonnet-20240620",
                "max_tokens": 1024,
                "system": system_prompt,
                "messages": messages,
                "temperature": temperature,
            }
            if anthropic_tools:
                kwargs["tools"] = anthropic_tools

            response = await self.client.messages.create(**kwargs)
            
            # Format the output into standard structure
            tool_calls = []
            content_text = ""
            for block in response.content:
                if block.type == "text":
                    content_text += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "args": block.input
                    })

            return {
                "content": content_text,
                "tool_calls": tool_calls,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }

        except Exception as e:
            logger.exception("Anthropic client call failed")
            raise e


anthropic_service = AnthropicService()

