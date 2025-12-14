"""
Tests for unified error handling middleware.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from exceptions import (
    AuthenticationError,
    ProblemGenerationError,
    SpeechProcessingError,
    ScoringError,
    RateLimitExceededError,
    ExternalAPIError,
    ValidationError
)


client = TestClient(app)


def test_health_check():
    """Test that health check endpoint works."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_404_error_handling():
    """Test that 404 errors return unified error format."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "user_message" in data["error"]
    assert data["error"]["code"] == "HTTP_404"


def test_validation_error_handling():
    """Test that validation errors return unified error format."""
    # Send invalid request to problems endpoint
    response = client.post(
        "/api/problems/generate",
        json={"task_type": "invalid_task"}  # Invalid task type
    )
    
    # Should return 400 or 422 with error format
    assert response.status_code in [400, 422]
    
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "user_message" in data["error"]


def test_method_not_allowed_error():
    """Test that method not allowed errors return unified format."""
    response = client.get("/api/problems/generate")  # Should be POST
    assert response.status_code == 405
    
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]


def test_custom_exception_structure():
    """Test that custom exceptions have correct structure."""
    exc = AuthenticationError("Test auth error")
    assert exc.error_code == "AUTH_ERROR"
    assert exc.user_message == "ログインに失敗しました。もう一度お試しください。"
    
    exc = ProblemGenerationError("Test problem error")
    assert exc.error_code == "PROBLEM_GENERATION_ERROR"
    
    exc = SpeechProcessingError("Test speech error")
    assert exc.error_code == "SPEECH_PROCESSING_ERROR"
    
    exc = ScoringError("Test scoring error")
    assert exc.error_code == "SCORING_ERROR"
    
    exc = RateLimitExceededError("Test rate limit")
    assert exc.error_code == "RATE_LIMIT_EXCEEDED"
    
    exc = ExternalAPIError("OpenAI", "Test API error")
    assert exc.error_code == "EXTERNAL_API_ERROR"
    assert exc.service == "OpenAI"
    
    exc = ValidationError("Test validation", field="test_field")
    assert exc.error_code == "VALIDATION_ERROR"
    assert exc.details["field"] == "test_field"


def test_custom_user_messages():
    """Test that custom user messages can be provided."""
    exc = AuthenticationError(
        message="Internal auth failure",
        user_message="カスタムメッセージ"
    )
    assert exc.message == "Internal auth failure"
    assert exc.user_message == "カスタムメッセージ"


def test_exception_with_details():
    """Test that exceptions can include additional details."""
    exc = ValidationError(
        message="Validation failed",
        user_message="入力エラー",
        field="email"
    )
    assert exc.details["field"] == "email"
    
    exc = ExternalAPIError("OpenAI", "Rate limit")
    assert exc.details["service"] == "OpenAI"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
