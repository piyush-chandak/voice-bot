from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the LLM provider (e.g. 'ollama', 'anthropic', 'openai')."""
        pass

    @abstractmethod
    async def generate_message(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Generate assistant response with optional tool execution requests."""
        pass


def get_llm_provider() -> BaseLLMProvider:
    from app.core.config import settings
    from app.integrations.anthropic import anthropic_service
    from app.integrations.openai import openai_service
    from app.integrations.gemini import gemini_service

    provider = (settings.LLM_PROVIDER or "gemini").lower().strip()
    if provider in ["claude", "anthropic"]:
        return anthropic_service
    elif provider in ["openai", "azure", "azure_openai"]:
        return openai_service
    elif provider in ["gemini", "google"]:
        return gemini_service
    return gemini_service

