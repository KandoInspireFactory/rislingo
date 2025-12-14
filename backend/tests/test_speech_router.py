"""
Tests for speech router endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO

from main import app
from exceptions import SpeechProcessingError, ExternalAPIError


client = TestClient(app)


class TestTranscribeEndpoint:
    """Test /api/speech/transcribe endpoint."""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self):
        """Test successful audio transcription."""
        # Create fake audio file
        audio_data = b"fake audio data" * 100
        files = {
            "audio_file": ("test.mp3", BytesIO(audio_data), "audio/mpeg")
        }
        data = {
            "problem_id": "test-problem-123"
        }
        
        with patch("routers.speech.get_speech_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.transcribe_audio = AsyncMock(return_value="This is a test transcription")
            mock_get_service.return_value = mock_service
            
            response = client.post("/api/speech/transcribe", files=files, data=data)
            
            assert response.status_code == 200
            json_data = response.json()
            assert "transcript" in json_data
            assert "processing_time" in json_data
            assert json_data["transcript"] == "This is a test transcription"
            assert isinstance(json_data["processing_time"], (int, float))
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_missing_file(self):
        """Test transcription without audio file."""
        data = {
            "problem_id": "test-problem-123"
        }
        
        response = client.post("/api/speech/transcribe", data=data)
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_missing_problem_id(self):
        """Test transcription without problem_id."""
        audio_data = b"fake audio data" * 100
        files = {
            "audio_file": ("test.mp3", BytesIO(audio_data), "audio/mpeg")
        }
        
        response = client.post("/api/speech/transcribe", files=files)
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_unsupported_format(self):
        """Test transcription with unsupported file format."""
        audio_data = b"fake audio data" * 100
        files = {
            "audio_file": ("test.txt", BytesIO(audio_data), "text/plain")
        }
        data = {
            "problem_id": "test-problem-123"
        }
        
        response = client.post("/api/speech/transcribe", files=files, data=data)
        
        assert response.status_code == 400
        assert "サポートされていないファイル形式" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_empty_file(self):
        """Test transcription with empty audio file."""
        files = {
            "audio_file": ("test.mp3", BytesIO(b""), "audio/mpeg")
        }
        data = {
            "problem_id": "test-problem-123"
        }
        
        response = client.post("/api/speech/transcribe", files=files, data=data)
        
        assert response.status_code == 400
        assert "音声ファイルが空です" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_supported_formats(self):
        """Test transcription with various supported audio formats."""
        supported_formats = [
            ("test.mp3", "audio/mpeg"),
            ("test.mp3", "audio/mp3"),
            ("test.wav", "audio/wav"),
            ("test.wav", "audio/wave"),
            ("test.wav", "audio/x-wav"),
            ("test.webm", "audio/webm"),
            ("test.ogg", "audio/ogg"),
            ("test.flac", "audio/flac"),
            ("test.m4a", "audio/m4a"),
            ("test.mp4", "audio/mp4"),
        ]
        
        for filename, content_type in supported_formats:
            audio_data = b"fake audio data" * 100
            files = {
                "audio_file": (filename, BytesIO(audio_data), content_type)
            }
            data = {
                "problem_id": "test-problem-123"
            }
            
            with patch("routers.speech.get_speech_service") as mock_get_service:
                mock_service = MagicMock()
                mock_service.transcribe_audio = AsyncMock(return_value="Test transcript")
                mock_get_service.return_value = mock_service
                
                response = client.post("/api/speech/transcribe", files=files, data=data)
                
                assert response.status_code == 200, f"Failed for {content_type}"
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_speech_processing_error(self):
        """Test transcription with speech processing error."""
        audio_data = b"fake audio data" * 100
        files = {
            "audio_file": ("test.mp3", BytesIO(audio_data), "audio/mpeg")
        }
        data = {
            "problem_id": "test-problem-123"
        }
        
        with patch("routers.speech.get_speech_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.transcribe_audio = AsyncMock(
                side_effect=SpeechProcessingError("音声の文字起こしに失敗しました")
            )
            mock_get_service.return_value = mock_service
            
            response = client.post("/api/speech/transcribe", files=files, data=data)
            
            assert response.status_code == 500
            assert "音声の文字起こしに失敗しました" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_external_api_error(self):
        """Test transcription with external API error."""
        audio_data = b"fake audio data" * 100
        files = {
            "audio_file": ("test.mp3", BytesIO(audio_data), "audio/mpeg")
        }
        data = {
            "problem_id": "test-problem-123"
        }
        
        with patch("routers.speech.get_speech_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.transcribe_audio = AsyncMock(
                side_effect=ExternalAPIError("OpenAI", "Rate limit exceeded")
            )
            mock_get_service.return_value = mock_service
            
            response = client.post("/api/speech/transcribe", files=files, data=data)
            
            assert response.status_code == 503
            assert "外部サービスとの通信に失敗しました" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_unexpected_error(self):
        """Test transcription with unexpected error."""
        audio_data = b"fake audio data" * 100
        files = {
            "audio_file": ("test.mp3", BytesIO(audio_data), "audio/mpeg")
        }
        data = {
            "problem_id": "test-problem-123"
        }
        
        with patch("routers.speech.get_speech_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.transcribe_audio = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            mock_get_service.return_value = mock_service
            
            response = client.post("/api/speech/transcribe", files=files, data=data)
            
            assert response.status_code == 500
            assert "予期しないエラー" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_processing_time(self):
        """Test that processing time is included in response."""
        audio_data = b"fake audio data" * 100
        files = {
            "audio_file": ("test.mp3", BytesIO(audio_data), "audio/mpeg")
        }
        data = {
            "problem_id": "test-problem-123"
        }
        
        with patch("routers.speech.get_speech_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.transcribe_audio = AsyncMock(return_value="Test transcript")
            mock_get_service.return_value = mock_service
            
            response = client.post("/api/speech/transcribe", files=files, data=data)
            
            assert response.status_code == 200
            json_data = response.json()
            assert "processing_time" in json_data
            assert json_data["processing_time"] >= 0
            assert json_data["processing_time"] < 10  # Should be fast in tests
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_no_content_type(self):
        """Test transcription with file missing content type."""
        audio_data = b"fake audio data" * 100
        files = {
            "audio_file": ("test.mp3", BytesIO(audio_data), None)
        }
        data = {
            "problem_id": "test-problem-123"
        }
        
        with patch("routers.speech.get_speech_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.transcribe_audio = AsyncMock(return_value="Test transcript")
            mock_get_service.return_value = mock_service
            
            response = client.post("/api/speech/transcribe", files=files, data=data)
            
            # When content_type is None, FastAPI assigns a default type
            # The endpoint should still work
            assert response.status_code == 200
