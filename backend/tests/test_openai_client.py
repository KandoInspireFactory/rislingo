"""
Tests for OpenAI client implementation.
"""
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from services.openai_client import OpenAIClient, get_openai_client
from exceptions import ExternalAPIError, SpeechProcessingError, ScoringError, ProblemGenerationError


class TestOpenAIClientInitialization:
    """Test OpenAI client initialization."""
    
    def test_client_initialization_with_api_key(self):
        """Test client can be initialized with API key."""
        client = OpenAIClient(api_key="test-key-123")
        assert client.api_key == "test-key-123"
        assert client.timeout == 30
        assert client.gpt4_model == "gpt-4"
        assert client.whisper_model == "whisper-1"
        assert client.tts_model == "tts-1"
    
    def test_client_initialization_without_api_key_raises_error(self):
        """Test client raises error when no API key is provided."""
        # Temporarily remove env var if it exists
        original_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        try:
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OpenAIClient()
        finally:
            # Restore original key
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key
    
    def test_client_initialization_with_custom_timeout(self):
        """Test client can be initialized with custom timeout."""
        client = OpenAIClient(api_key="test-key-123", timeout=60)
        assert client.timeout == 60
    
    def test_get_openai_client_singleton(self):
        """Test singleton pattern for client."""
        # This test requires OPENAI_API_KEY to be set
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        client1 = get_openai_client()
        client2 = get_openai_client()
        assert client1 is client2


class TestOpenAIClientMethods:
    """Test OpenAI client methods with mocked API calls."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return OpenAIClient(api_key="test-key-123")
    
    @pytest.mark.asyncio
    async def test_call_gpt4_success(self, client):
        """Test successful GPT-4 API call."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await client.call_gpt4("Test prompt")
            
            assert result == "Test response"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_gpt4_with_system_message(self, client):
        """Test GPT-4 call with system message."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await client.call_gpt4(
                prompt="Test prompt",
                system_message="You are a test assistant"
            )
            
            assert result == "Test response"
            call_args = mock_create.call_args
            messages = call_args.kwargs['messages']
            assert len(messages) == 2
            assert messages[0]['role'] == 'system'
            assert messages[1]['role'] == 'user'
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, client):
        """Test successful audio transcription."""
        mock_response = MagicMock()
        mock_response.text = "Transcribed text"
        
        with patch.object(client.client.audio.transcriptions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            audio_bytes = b"fake audio data"
            result = await client.transcribe_audio(audio_bytes)
            
            assert result == "Transcribed text"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_speech_success(self, client):
        """Test successful speech generation."""
        mock_response = MagicMock()
        mock_response.content = b"fake audio content"
        
        with patch.object(client.client.audio.speech, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await client.generate_speech("Test text")
            
            assert result == b"fake audio content"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_problem_success(self, client):
        """Test successful problem generation."""
        mock_gpt4_response = """{
            "reading_text": "Test reading passage",
            "lecture_script": "Test lecture script",
            "question": "Test question"
        }"""
        
        with patch.object(client, 'call_gpt4', new_callable=AsyncMock) as mock_gpt4:
            mock_gpt4.return_value = mock_gpt4_response
            
            result = await client.generate_problem("psychology")
            
            assert "reading_text" in result
            assert "lecture_script" in result
            assert "question" in result
            assert result["reading_text"] == "Test reading passage"
    
    @pytest.mark.asyncio
    async def test_generate_problem_invalid_json(self, client):
        """Test problem generation with invalid JSON response."""
        with patch.object(client, 'call_gpt4', new_callable=AsyncMock) as mock_gpt4:
            mock_gpt4.return_value = "Invalid JSON"
            
            with pytest.raises(ProblemGenerationError, match="Failed to generate valid problem format"):
                await client.generate_problem("psychology")
    
    @pytest.mark.asyncio
    async def test_score_response_success(self, client):
        """Test successful response scoring."""
        mock_gpt4_response = """{
            "delivery_score": 3,
            "delivery_feedback": "Good delivery",
            "language_use_score": 3,
            "language_use_feedback": "Good language use",
            "topic_dev_score": 4,
            "topic_dev_feedback": "Excellent topic development",
            "overall_score": 3,
            "improvement_tips": ["Tip 1", "Tip 2"]
        }"""
        
        with patch.object(client, 'call_gpt4', new_callable=AsyncMock) as mock_gpt4:
            mock_gpt4.return_value = mock_gpt4_response
            
            result = await client.score_response(
                transcript="Test transcript",
                reading_text="Test reading",
                lecture_script="Test lecture",
                question="Test question"
            )
            
            assert result["delivery_score"] == 3
            assert result["overall_score"] == 3
            assert len(result["improvement_tips"]) == 2
    
    @pytest.mark.asyncio
    async def test_score_response_invalid_score_range(self, client):
        """Test scoring with invalid score range."""
        mock_gpt4_response = """{
            "delivery_score": 5,
            "delivery_feedback": "Good delivery",
            "language_use_score": 3,
            "language_use_feedback": "Good language use",
            "topic_dev_score": 4,
            "topic_dev_feedback": "Excellent topic development",
            "overall_score": 3,
            "improvement_tips": ["Tip 1"]
        }"""
        
        with patch.object(client, 'call_gpt4', new_callable=AsyncMock) as mock_gpt4:
            mock_gpt4.return_value = mock_gpt4_response
            
            with pytest.raises(ScoringError, match="Invalid score"):
                await client.score_response(
                    transcript="Test transcript",
                    reading_text="Test reading",
                    lecture_script="Test lecture",
                    question="Test question"
                )
    
    @pytest.mark.asyncio
    async def test_generate_model_answer_success(self, client):
        """Test successful model answer generation."""
        mock_gpt4_response = """{
            "model_answer": "This is a model answer",
            "highlighted_phrases": [
                {
                    "text": "First of all",
                    "category": "transition",
                    "useful_for_writing": true
                }
            ]
        }"""
        
        with patch.object(client, 'call_gpt4', new_callable=AsyncMock) as mock_gpt4:
            mock_gpt4.return_value = mock_gpt4_response
            
            result = await client.generate_model_answer(
                reading_text="Test reading",
                lecture_script="Test lecture",
                question="Test question"
            )
            
            assert "model_answer" in result
            assert "highlighted_phrases" in result
            assert result["model_answer"] == "This is a model answer"
            assert len(result["highlighted_phrases"]) == 1


class TestErrorHandling:
    """Test error handling in OpenAI client."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return OpenAIClient(api_key="test-key-123")
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, client):
        """Test handling of rate limit errors."""
        from openai import RateLimitError
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = RateLimitError("Rate limit exceeded", response=MagicMock(), body=None)
            
            with pytest.raises(ExternalAPIError, match="Rate limit exceeded"):
                await client.call_gpt4("Test prompt")
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, client):
        """Test handling of timeout errors."""
        from openai import APITimeoutError
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = APITimeoutError(request=MagicMock())
            
            with pytest.raises(ExternalAPIError, match="Request timed out"):
                await client.call_gpt4("Test prompt")
    
    @pytest.mark.asyncio
    async def test_transcription_error_handling(self, client):
        """Test handling of transcription errors."""
        from openai import APIError
        
        with patch.object(client.client.audio.transcriptions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = APIError("API error", request=MagicMock(), body=None)
            
            with pytest.raises(SpeechProcessingError, match="Transcription failed"):
                await client.transcribe_audio(b"fake audio")
