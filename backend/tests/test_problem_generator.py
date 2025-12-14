"""
Tests for Problem Generator Service.
"""
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from services.problem_generator import ProblemGeneratorService, get_problem_generator
from exceptions import ProblemGenerationError


class TestProblemGeneratorService:
    """Test problem generator service."""
    
    @pytest.fixture
    def service(self):
        """Create a test service instance."""
        with patch('services.problem_generator.get_openai_client'):
            service = ProblemGeneratorService()
            service.openai_client = MagicMock()
            return service
    
    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service.openai_client is not None
        assert len(service.TOPIC_CATEGORIES) > 0
        assert "psychology" in service.TOPIC_CATEGORIES
        assert "biology" in service.TOPIC_CATEGORIES
    
    def test_select_random_topic(self, service):
        """Test random topic selection."""
        topic = service._select_random_topic()
        assert topic in service.TOPIC_CATEGORIES
    
    @pytest.mark.asyncio
    async def test_generate_problem_success(self, service):
        """Test successful problem generation."""
        # Mock OpenAI client responses
        mock_problem_data = {
            "reading_text": "Test reading passage about psychology",
            "lecture_script": "Test lecture script with examples",
            "question": "Test question about the concept"
        }
        service.openai_client.generate_problem = AsyncMock(return_value=mock_problem_data)
        service.openai_client.generate_speech = AsyncMock(return_value=b"fake audio data")
        
        # Mock file writing
        with patch('builtins.open', mock_open()) as mock_file:
            result = await service.generate_problem(task_type="task3", topic_category="psychology")
        
        # Verify result structure
        assert "problem_id" in result
        assert "reading_text" in result
        assert "lecture_script" in result
        assert "lecture_audio_url" in result
        assert "question" in result
        assert "topic_category" in result
        
        # Verify content
        assert result["reading_text"] == "Test reading passage about psychology"
        assert result["lecture_script"] == "Test lecture script with examples"
        assert result["question"] == "Test question about the concept"
        assert result["topic_category"] == "psychology"
        assert "/audio/" in result["lecture_audio_url"]
        
        # Verify OpenAI client was called
        service.openai_client.generate_problem.assert_called_once()
        service.openai_client.generate_speech.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_problem_random_topic(self, service):
        """Test problem generation with random topic selection."""
        mock_problem_data = {
            "reading_text": "Test reading",
            "lecture_script": "Test lecture",
            "question": "Test question"
        }
        service.openai_client.generate_problem = AsyncMock(return_value=mock_problem_data)
        service.openai_client.generate_speech = AsyncMock(return_value=b"fake audio")
        
        with patch('builtins.open', mock_open()):
            result = await service.generate_problem(task_type="task3", topic_category=None)
        
        # Should have selected a random topic
        assert result["topic_category"] in service.TOPIC_CATEGORIES
    
    @pytest.mark.asyncio
    async def test_generate_problem_invalid_topic_uses_random(self, service):
        """Test that invalid topic category falls back to random selection."""
        mock_problem_data = {
            "reading_text": "Test reading",
            "lecture_script": "Test lecture",
            "question": "Test question"
        }
        service.openai_client.generate_problem = AsyncMock(return_value=mock_problem_data)
        service.openai_client.generate_speech = AsyncMock(return_value=b"fake audio")
        
        with patch('builtins.open', mock_open()):
            result = await service.generate_problem(task_type="task3", topic_category="invalid_topic")
        
        # Should have fallen back to a valid topic
        assert result["topic_category"] in service.TOPIC_CATEGORIES
    
    @pytest.mark.asyncio
    async def test_generate_problem_openai_error(self, service):
        """Test problem generation handles OpenAI errors."""
        service.openai_client.generate_problem = AsyncMock(side_effect=Exception("API error"))
        
        with pytest.raises(ProblemGenerationError, match="Failed to generate problem"):
            await service.generate_problem(task_type="task3", topic_category="psychology")
    
    @pytest.mark.asyncio
    async def test_generate_lecture_audio_success(self, service):
        """Test successful lecture audio generation."""
        service.openai_client.generate_speech = AsyncMock(return_value=b"fake audio data")
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = await service.generate_lecture_audio(
                lecture_script="Test lecture script",
                problem_id="test-id-123"
            )
        
        assert "/audio/" in result
        assert "test-id-123" in result
        service.openai_client.generate_speech.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_lecture_audio_without_problem_id(self, service):
        """Test audio generation creates UUID when no problem_id provided."""
        service.openai_client.generate_speech = AsyncMock(return_value=b"fake audio data")
        
        with patch('builtins.open', mock_open()):
            result = await service.generate_lecture_audio(lecture_script="Test lecture")
        
        assert "/audio/" in result
        assert ".mp3" in result
    
    @pytest.mark.asyncio
    async def test_generate_lecture_audio_error(self, service):
        """Test audio generation handles errors."""
        service.openai_client.generate_speech = AsyncMock(side_effect=Exception("TTS error"))
        
        with pytest.raises(ProblemGenerationError, match="Failed to generate audio"):
            await service.generate_lecture_audio(lecture_script="Test lecture")
    
    def test_get_problem_generator_singleton(self):
        """Test singleton pattern for problem generator."""
        with patch('services.problem_generator.get_openai_client'):
            generator1 = get_problem_generator()
            generator2 = get_problem_generator()
            assert generator1 is generator2


class TestProblemGeneratorIntegration:
    """Integration tests for problem generator (requires OpenAI API key)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
    async def test_generate_complete_problem_integration(self):
        """Test complete problem generation with real API (if key available)."""
        service = ProblemGeneratorService()
        
        # This will make real API calls
        result = await service.generate_problem(task_type="task3", topic_category="psychology")
        
        # Verify structure
        assert "problem_id" in result
        assert "reading_text" in result
        assert len(result["reading_text"]) > 50  # Should be substantial
        assert "lecture_script" in result
        assert len(result["lecture_script"]) > 100  # Should be substantial
        assert "question" in result
        assert len(result["question"]) > 10
        assert "lecture_audio_url" in result
        assert result["topic_category"] == "psychology"
        
        # Verify audio file was created
        audio_path = result["lecture_audio_url"].replace("/audio/", "backend/audio_files/")
        assert os.path.exists(audio_path)
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
