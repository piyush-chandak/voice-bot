import httpx
from app.core.config import settings
from app.core.logging import logger
from app.services.speech_service import SpeechService


class DeepgramSpeechService(SpeechService):
    async def transcribe(self, audio_data: bytes) -> str:
        api_key = settings.STT_KEY or settings.DEEPGRAM_API_KEY
        if not api_key:
            logger.info("Deepgram API key not found. Returning mock transcription.")
            return "Get location and find nearby tickets"

        logger.info("Transcribing audio with Deepgram API")
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "audio/wav",
                }
                model_name = settings.STT_MODEL or "nova-2"
                response = await client.post(
                    f"https://api.deepgram.com/v1/listen?model={model_name}&smart_format=true",
                    headers=headers,
                    content=audio_data,
                    timeout=30.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return (
                        data.get("results", {})
                        .get("channels", [{}])[0]
                        .get("alternatives", [{}])[0]
                        .get("transcript", "")
                    )
                else:
                    logger.error(
                        f"Deepgram API error: {response.text}",
                        extra={"status_code": response.status_code},
                    )
                    return "Fallback Deepgram transcription due to error"
        except Exception as e:
            logger.exception("Exception occurred during Deepgram transcription")
            return "Fallback Deepgram transcription due to exception"
            
            
def get_speech_provider() -> SpeechService:
    provider = settings.STT_PROVIDER.lower()
    if provider == "deepgram":
        return DeepgramSpeechService()
    return WhisperSpeechService()
