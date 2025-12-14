"""
Speech service for TOEFL Speaking Master.
Handles audio transcription using OpenAI Whisper API.
"""
import logging
from typing import Optional
from io import BytesIO

from services.openai_client import get_openai_client
from exceptions import SpeechProcessingError


logger = logging.getLogger(__name__)


class SpeechService:
    """
    Service for speech processing operations.
    
    Provides:
    - Audio transcription using Whisper API
    - Error handling and validation
    """
    
    def __init__(self):
        """Initialize speech service with OpenAI client."""
        self.openai_client = get_openai_client()
        logger.info("SpeechService initialized")
    
    async def transcribe_audio(
        self,
        audio_file: bytes,
        filename: str = "audio.mp3",
        language: str = "en"
    ) -> str:
        """
        Transcribe audio file to text using Whisper API.
        
        Args:
            audio_file: Audio file bytes (MP3, WAV, etc.)
            filename: Original filename (used for format detection)
            language: Language code (default: "en" for English)
            
        Returns:
            Transcribed text
            
        Raises:
            SpeechProcessingError: If transcription fails or audio is invalid
        """
        try:
            # Validate audio file
            if not audio_file or len(audio_file) == 0:
                raise SpeechProcessingError("音声ファイルが空です。")
            
            # Check file size (OpenAI limit is 25MB)
            max_size = 25 * 1024 * 1024  # 25MB in bytes
            if len(audio_file) > max_size:
                raise SpeechProcessingError(
                    f"音声ファイルが大きすぎます。最大サイズは25MBです。"
                )
            
            logger.info(f"Transcribing audio file: {filename} ({len(audio_file)} bytes)")
            
            # Call Whisper API through OpenAI client
            transcript = await self.openai_client.transcribe_audio(
                audio_file=audio_file,
                filename=filename,
                language=language
            )
            
            # Validate transcript
            if not transcript or len(transcript.strip()) == 0:
                logger.warning("Transcription returned empty text")
                raise SpeechProcessingError(
                    "音声の文字起こしに失敗しました。音声が明瞭でない可能性があります。"
                )
            
            logger.info(f"Transcription successful: {len(transcript)} characters")
            return transcript.strip()
            
        except SpeechProcessingError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error in transcription: {e}")
            raise SpeechProcessingError(
                f"音声の文字起こし中に予期しないエラーが発生しました: {str(e)}"
            )


# Singleton instance
_speech_service: Optional[SpeechService] = None


def get_speech_service() -> SpeechService:
    """
    Get or create singleton SpeechService instance.
    
    Returns:
        SpeechService instance
    """
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechService()
    return _speech_service
