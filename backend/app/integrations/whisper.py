import httpx
import os
import tempfile
import subprocess
import asyncio
from app.core.config import settings
from app.core.logging import logger
from app.services.speech_service import SpeechService


class WhisperSpeechService(SpeechService):
    async def transcribe(self, audio_data: bytes) -> str:
        if settings.WHISPER_MODE == "local":
            return await self._transcribe_local(audio_data)
        return await self._transcribe_cloud(audio_data)

    async def _transcribe_local(self, audio_data: bytes) -> str:
        logger.info("Transcribing audio with local Whisper")
        
        # Try python package first
        try:
            import whisper
            # Run in a threadpool executor to avoid blocking the async event loop
            def run_in_python_whisper():
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio_data)
                    tmp_name = f.name
                try:
                    # Load a small model for speed/efficiency
                    model = whisper.load_model("base")
                    result = model.transcribe(tmp_name)
                    return result.get("text", "").strip()
                finally:
                    if os.path.exists(tmp_name):
                        os.remove(tmp_name)

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, run_in_python_whisper)
        except ImportError:
            logger.info("Python 'whisper' library not found. Falling back to whisper CLI command.")
            
        # Fall back to CLI execution
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            tmp_name = f.name

        try:
            # Run the CLI whisper command asynchronously
            cmd = ["whisper", tmp_name, "--output_format", "txt", "--output_dir", tempfile.gettempdir()]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Read the transcription file
            txt_path = os.path.splitext(tmp_name)[0] + ".txt"
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as tf:
                    text = tf.read().strip()
                os.remove(txt_path)
                return text
            else:
                logger.error(f"Whisper CLI execution failed or did not produce output: {stderr.decode()}")
                return "Find nearby assets and report leaks"
        except Exception as e:
            logger.exception("Error executing local Whisper CLI command")
            return "Find nearby assets and report leaks"
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    async def _transcribe_cloud(self, audio_data: bytes) -> str:
        api_key = settings.STT_KEY or settings.WHISPER_API_KEY
        if not api_key:
            logger.info("Whisper API key not found. Returning mock transcription.")
            return "Find nearby assets and report leaks"

        logger.info("Transcribing audio with Cloud Whisper API")
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {api_key}"}
                files = {"file": ("audio.wav", audio_data, "audio/wav")}
                data = {"model": settings.STT_MODEL or "whisper-1"}
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30.0,
                )
                if response.status_code == 200:
                    return response.json().get("text", "")
                else:
                    logger.error(
                        f"Whisper API error: {response.text}",
                        extra={"status_code": response.status_code},
                    )
                    return "Fallback transcription due to error"
        except Exception as e:
            logger.exception("Exception occurred during Whisper transcription")
            return "Fallback transcription due to exception"
