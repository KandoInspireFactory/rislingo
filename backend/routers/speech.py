"""
Speech router for TOEFL Speaking Master API.
Handles audio transcription endpoints.
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
import logging
import time

from services.speech_service import get_speech_service
from exceptions import SpeechProcessingError, ExternalAPIError


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/speech",
    tags=["speech"]
)


# Response models
class TranscribeResponse(BaseModel):
    """Response model for audio transcription."""
    transcript: str = Field(description="Transcribed text from audio")
    processing_time: float = Field(description="Processing time in seconds")


@router.post("/transcribe", response_model=TranscribeResponse, status_code=status.HTTP_200_OK)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe (MP3, WAV, etc.)"),
    problem_id: str = Form(..., description="Problem ID associated with this recording")
):
    """
    Transcribe audio file to text using Whisper API.
    
    This endpoint:
    1. Receives an audio file from the user's recording
    2. Validates the file format and size
    3. Sends the audio to OpenAI Whisper API for transcription
    4. Returns the transcribed text
    
    Args:
        audio_file: Uploaded audio file (multipart/form-data)
        problem_id: ID of the problem this recording is for
        
    Returns:
        Transcribed text and processing time
        
    Raises:
        HTTPException: If transcription fails or file is invalid
    """
    start_time = time.time()
    
    try:
        logger.info(f"Received transcription request: problem_id={problem_id}, filename={audio_file.filename}, content_type={audio_file.content_type}")
        
        # Validate file type
        if not audio_file.content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ファイルタイプを判定できません。"
            )
        
        # Accept common audio formats
        allowed_types = [
            "audio/mpeg",      # MP3
            "audio/mp3",       # MP3 (alternative)
            "audio/wav",       # WAV
            "audio/wave",      # WAV (alternative)
            "audio/x-wav",     # WAV (alternative)
            "audio/webm",      # WebM
            "audio/webm;codecs=opus",  # WebM with Opus codec
            "audio/ogg",       # OGG
            "audio/flac",      # FLAC
            "audio/m4a",       # M4A
            "audio/mp4",       # MP4 audio
        ]
        
        if audio_file.content_type not in allowed_types:
            logger.warning(f"Unsupported file type: {audio_file.content_type}")
            logger.info(f"Allowed types: {allowed_types}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"サポートされていないファイル形式です: {audio_file.content_type}。対応形式: MP3, WAV, WebM, OGG, FLAC, M4A"
            )
        
        # Read audio file bytes
        audio_bytes = await audio_file.read()
        
        if not audio_bytes or len(audio_bytes) == 0:
            logger.error(f"Empty audio file received. Filename: {audio_file.filename}, Content-Type: {audio_file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="音声ファイルが空です。"
            )
        
        logger.info(f"Audio file size: {len(audio_bytes)} bytes")
        
        # Log first few bytes for debugging (only in development)
        if len(audio_bytes) > 0:
            first_bytes = audio_bytes[:20].hex() if len(audio_bytes) >= 20 else audio_bytes.hex()
            logger.info(f"First bytes (hex): {first_bytes}")
            
        # Check if the audio data looks valid
        if len(audio_bytes) < 100:  # Very small files are likely invalid
            logger.warning(f"Audio file is very small ({len(audio_bytes)} bytes), might be invalid")
            
        # For WebM files, check for basic WebM signature
        if audio_file.content_type and 'webm' in audio_file.content_type.lower():
            if not audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):
                logger.warning("WebM file doesn't start with expected signature")
        
        # Transcribe audio
        speech_service = get_speech_service()
        transcript = await speech_service.transcribe_audio(
            audio_file=audio_bytes,
            filename=audio_file.filename or "audio.mp3",
            language="en"
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Transcription completed in {processing_time:.2f}s: {len(transcript)} characters")
        
        # Return response
        return TranscribeResponse(
            transcript=transcript,
            processing_time=round(processing_time, 2)
        )
        
    except SpeechProcessingError as e:
        logger.error(f"Speech processing error: {e}")
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except ExternalAPIError as e:
        logger.error(f"External API error: {e}")
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="外部サービスとの通信に失敗しました。しばらく待ってから再試行してください。"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in transcription endpoint: {e}")
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="予期しないエラーが発生しました。"
        )
