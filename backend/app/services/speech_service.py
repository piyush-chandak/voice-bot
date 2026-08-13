from abc import ABC, abstractmethod


class SpeechService(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio bytes to text."""
        pass
