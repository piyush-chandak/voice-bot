import json
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.integrations.base_llm import BaseLLMProvider


class GeminiService(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "gemini"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_message(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("Gemini API key is not configured. Please set GEMINI_API_KEY.")

        model_name = settings.LLM_MODEL or "gemini-2.0-flash"
        if not model_name.startswith("gemini"):
            model_name = "gemini-2.0-flash"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        # 1. Format System Instruction
        payload = {}
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        # 2. Format Tools (Function Declarations)
        if tools:
            declarations = []
            for tool in tools:
                parameters = tool.get("input_schema", {})
                if not parameters:
                    parameters = {"type": "OBJECT", "properties": {}}
                
                # Convert lowercase type names to uppercase
                def convert_schema_types(schema: Any) -> Any:
                    if isinstance(schema, dict):
                        new_schema = {}
                        for k, v in schema.items():
                            if k == "type" and isinstance(v, str):
                                new_schema[k] = v.upper()
                            else:
                                new_schema[k] = convert_schema_types(v)
                        return new_schema
                    elif isinstance(schema, list):
                        return [convert_schema_types(item) for item in schema]
                    return schema

                parameters = convert_schema_types(parameters)

                declarations.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": parameters
                })
            payload["tools"] = [{"functionDeclarations": declarations}]

        # 3. Format Messages Contents
        contents = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                continue
            elif role == "tool":
                try:
                    parsed_res = json.loads(content)
                except Exception:
                    parsed_res = {"output": content}

                contents.append({
                    "role": "user",
                    "parts": [
                        {
                            "functionResponse": {
                                "name": msg.get("name") or "tool_call",
                                "response": {"output": parsed_res}
                            }
                        }
                    ]
                })
            elif role == "assistant" and msg.get("tool_calls"):
                parts = []
                if content:
                    parts.append({"text": content})
                for tc in msg["tool_calls"]:
                    fn_part = {
                        "functionCall": {
                            "name": tc["name"],
                            "args": tc["args"]
                        }
                    }
                    if "thought_signature" in tc and tc["thought_signature"]:
                        fn_part["thoughtSignature"] = tc["thought_signature"]
                    elif "thoughtSignature" in tc and tc["thoughtSignature"]:
                        fn_part["thoughtSignature"] = tc["thoughtSignature"]
                    parts.append(fn_part)
                contents.append({
                    "role": "model",
                    "parts": parts
                })
            else:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content or ""}]
                })

        payload["contents"] = contents
        payload["generationConfig"] = {
            "temperature": temperature,
        }

        try:
            logger.info(f"Sending request to Gemini API: {model_name}")
            response = await self.client.post(url, json=payload)
            if response.status_code != 200:
                logger.error(f"Gemini API returned error {response.status_code}: {response.text}")
                raise Exception(f"Gemini API error {response.status_code}: {response.text}")

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return {
                    "content": "No response returned from Gemini.",
                    "tool_calls": [],
                    "usage": {"input_tokens": 0, "output_tokens": 0}
                }

            first_candidate = candidates[0]
            content_parts = first_candidate.get("content", {}).get("parts", [])
            
            content_text = ""
            tool_calls = []

            for part in content_parts:
                if "text" in part:
                    content_text += part["text"]
                if "functionCall" in part:
                    fn_call = part["functionCall"]
                    tool_calls.append({
                        "id": "gemini_call",
                        "name": fn_call["name"],
                        "args": fn_call.get("args") or {},
                        "thought_signature": part.get("thoughtSignature")
                    })

            usage_metadata = data.get("usageMetadata", {})
            return {
                "content": content_text,
                "tool_calls": tool_calls,
                "usage": {
                    "input_tokens": usage_metadata.get("promptTokenCount", 0),
                    "output_tokens": usage_metadata.get("candidatesTokenCount", 0)
                }
            }

        except Exception as e:
            logger.exception("Gemini API call failed")
            raise e


gemini_service = GeminiService()
