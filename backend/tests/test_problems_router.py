"""
Tests for problems router endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from main import app
from exceptions import ProblemGenerationError


client = TestClient(app)


class TestProblemsRouter:
    """Test problems router endpoints."""
    
    def test_generate_problem_success(self):
        """Test successful problem generation endpoint."""
        mock_problem_data = {
            "problem_id": "test-id-123",
            "reading_text": "Test reading passage",
            "lecture_script": "Test lecture script",
            "lecture_audio_url": "/audio/lecture_test-id-123.mp3",
            "question": "Test question",
            "topic_category": "psychology",
            "created_at": "2024-01-01T00:00:00"
        }
        
        with patch('routers.problems.get_problem_generator') as mock_get_generator:
            mock_generator = AsyncMock()
            mock_generator.generate_problem = AsyncMock(return_value=mock_problem_data)
            mock_get_generator.return_value = mock_generator
            
            response = client.post(
                "/api/problems/generate",
                json={"task_type": "task3", "topic_category": "psychology"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["problem_id"] == "test-id-123"
        assert data["reading_text"] == "Test reading passage"
        assert data["lecture_script"] == "Test lecture script"
        assert data["lecture_audio_url"] == "/audio/lecture_test-id-123.mp3"
        assert data["question"] == "Test question"
        assert data["topic_category"] == "psychology"
    
    def test_generate_problem_default_values(self):
        """Test problem generation with default values."""
        mock_problem_data = {
            "problem_id": "test-id-456",
            "reading_text": "Test reading",
            "lecture_script": "Test lecture",
            "lecture_audio_url": "/audio/lecture_test-id-456.mp3",
            "question": "Test question",
            "topic_category": "biology",
            "created_at": "2024-01-01T00:00:00"
        }
        
        with patch('routers.problems.get_problem_generator') as mock_get_generator:
            mock_generator = AsyncMock()
            mock_generator.generate_problem = AsyncMock(return_value=mock_problem_data)
            mock_get_generator.return_value = mock_generator
            
            response = client.post("/api/problems/generate", json={})
        
        assert response.status_code == 201
        data = response.json()
        assert "problem_id" in data
    
    def test_generate_problem_invalid_task_type(self):
        """Test problem generation with invalid task type."""
        response = client.post(
            "/api/problems/generate",
            json={"task_type": "task1", "topic_category": "psychology"}
        )
        
        assert response.status_code == 400
        assert "task3" in response.json()["detail"]
    
    def test_generate_problem_service_error(self):
        """Test problem generation handles service errors."""
        with patch('routers.problems.get_problem_generator') as mock_get_generator:
            mock_generator = AsyncMock()
            mock_generator.generate_problem = AsyncMock(
                side_effect=ProblemGenerationError("Test error")
            )
            mock_get_generator.return_value = mock_generator
            
            response = client.post(
                "/api/problems/generate",
                json={"task_type": "task3"}
            )
        
        assert response.status_code == 500
        assert "問題の生成に失敗しました" in response.json()["detail"]
    
    def test_generate_problem_unexpected_error(self):
        """Test problem generation handles unexpected errors."""
        with patch('routers.problems.get_problem_generator') as mock_get_generator:
            mock_generator = AsyncMock()
            mock_generator.generate_problem = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            mock_get_generator.return_value = mock_generator
            
            response = client.post(
                "/api/problems/generate",
                json={"task_type": "task3"}
            )
        
        assert response.status_code == 500
        assert "予期しないエラー" in response.json()["detail"]
