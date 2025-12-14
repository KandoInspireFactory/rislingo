"""
Tests for SpeechService implementation.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.speech_service import SpeechService, get_speech_service
from exceptions import SpeechProcessingError


class TestSpeechServiceInitialization:
    """Test SpeechService initialization."""
    
    def test_service_initialization(self):
        """Test service can be initialized."""
        with patch("services.speech_service.get_openai_client") as mock_get_client:
            mock_get_client.return_value = MagicMock()
            service = SpeechService()
            assert service.openai_client is not None
    
    def test_get_speech_service_singleton(self):
        """Test singleton pattern for service."""
        with patch("services.speech_service.get_openai_client") as mock_get_client:
            mock_get_client.return_value = MagicMock()
            service1 = get_speech_service()
            service2 = get_speech_service()
            assert service1 is service2


class TestTranscribeAudio:
    """Test audio transcription functionality."""
    
    @pytest.fixture
    def service(self):
        """Create a test service."""
        with patch("services.speech_service.get_openai_client") as mock_get_client:
            mock_get_client.return_value = MagicMock()
            return SpeechService()
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, service):
        """Test successful audio transcription."""
        audio_bytes = b"fake audio data" * 100
        expected_transcript = "This is a test transcription"
        
        with patch.object(service.openai_client, 'transcribe_audio', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = expected_transcript
            
            result = await service.transcribe_audio(audio_bytes, "test.mp3")
            
            assert result == expected_transcript
            mock_transcribe.assert_called_once_with(
                audio_file=audio_bytes,
                filename="test.mp3",
                language="en"
            )
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_whitespace(self, service):
        """Test transcription strips whitespace."""
        audio_bytes = b"fake audio data" * 100
        transcript_with_whitespace = "  This is a test  \n"
        
        with patch.object(service.openai_client, 'transcribe_audio', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = transcript_with_whitespace
            
            result = await service.transcribe_audio(audio_bytes, "test.mp3")
            
            assert result == "This is a test"
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_empty_file(self, service):
        """Test transcription with empty audio file."""
        with pytest.raises(SpeechProcessingError, match="音声ファイルが空です"):
            await service.transcribe_audio(b"", "test.mp3")
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_none_file(self, service):
        """Test transcription with None audio file."""
        with pytest.raises(SpeechProcessingError, match="音声ファイルが空です"):
            await service.transcribe_audio(None, "test.mp3")
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_file_too_large(self, service):
        """Test transcription with file exceeding size limit."""
        # Create audio bytes larger than 25MB
        large_audio = b"x" * (26 * 1024 * 1024)
        
        with pytest.raises(SpeechProcessingError, match="音声ファイルが大きすぎます"):
            await service.transcribe_audio(large_audio, "test.mp3")
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_empty_transcript(self, service):
        """Test transcription returning empty text."""
        audio_bytes = b"fake audio data" * 100
        
        with patch.object(service.openai_client, 'transcribe_audio', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = ""
            
            with pytest.raises(SpeechProcessingError, match="音声の文字起こしに失敗しました"):
                await service.transcribe_audio(audio_bytes, "test.mp3")
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_whitespace_only_transcript(self, service):
        """Test transcription returning only whitespace."""
        audio_bytes = b"fake audio data" * 100
        
        with patch.object(service.openai_client, 'transcribe_audio', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = "   \n\t  "
            
            with pytest.raises(SpeechProcessingError, match="音声の文字起こしに失敗しました"):
                await service.transcribe_audio(audio_bytes, "test.mp3")
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_custom_language(self, service):
        """Test transcription with custom language."""
        audio_bytes = b"fake audio data" * 100
        expected_transcript = "Test transcript"
        
        with patch.object(service.openai_client, 'transcribe_audio', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = expected_transcript
            
            result = await service.transcribe_audio(audio_bytes, "test.mp3", language="ja")
            
            assert result == expected_transcript
            mock_transcribe.assert_called_once_with(
                audio_file=audio_bytes,
                filename="test.mp3",
                language="ja"
            )
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_api_error(self, service):
        """Test transcription with API error."""
        audio_bytes = b"fake audio data" * 100
        
        with patch.object(service.openai_client, 'transcribe_audio', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.side_effect = SpeechProcessingError("API error")
            
            with pytest.raises(SpeechProcessingError, match="API error"):
                await service.transcribe_audio(audio_bytes, "test.mp3")
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_unexpected_error(self, service):
        """Test transcription with unexpected error."""
        audio_bytes = b"fake audio data" * 100
        
        with patch.object(service.openai_client, 'transcribe_audio', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.side_effect = Exception("Unexpected error")
            
            with pytest.raises(SpeechProcessingError, match="予期しないエラー"):
                await service.transcribe_audio(audio_bytes, "test.mp3")


class TestTranscriptionValidation:
    """Test audio transcription validation logic."""
    
    @pytest.fixture
    def service(self):
        """Create a test service."""
        with patch("services.speech_service.get_openai_client") as mock_get_client:
            mock_get_client.return_value = MagicMock()
            return SpeechService()
    
    @pytest.mark.asyncio
    async def test_valid_audio_sizes(self, service):
        """Test various valid audio file sizes."""
        test_sizes = [
            1024,           # 1KB
            1024 * 1024,    # 1MB
            10 * 1024 * 1024,  # 10MB
            24 * 1024 * 1024,  # 24MB (just under limit)
        ]
        
        for size in test_sizes:
            audio_bytes = b"x" * size
            
            with patch.object(service.openai_client, 'transcribe_audio', new_callable=AsyncMock) as mock_transcribe:
                mock_transcribe.return_value = "Test transcript"
                
                result = await service.transcribe_audio(audio_bytes, "test.mp3")
                assert result == "Test transcript"
    
    @pytest.mark.asyncio
    async def test_transcription_logging(self, service):
        """Test that transcription logs appropriately."""
        audio_bytes = b"fake audio data" * 100
        
        with patch.object(service.openai_client, 'transcribe_audio', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = "Test transcript"
            
            result = await service.transcribe_audio(audio_bytes, "test.mp3")
            
            assert result == "Test transcript"
