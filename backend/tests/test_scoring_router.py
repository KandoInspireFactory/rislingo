"""
Unit tests for scoring router endpoints.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient

from main import app
from services.scoring_service import ScoringResult, ScoringDetail
from exceptions import ScoringError, ExternalAPIError


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    mock_session = MagicMock()
    return mock_session


@pytest.fixture
def mock_scoring_service():
    """Mock scoring service."""
    mock_service = MagicMock()
    return mock_service


@pytest.fixture
def client_with_mocks(mock_db_session, mock_scoring_service):
    """Test client with mocked dependencies."""
    def override_get_db():
        yield mock_db_session
    
    def override_get_scoring_service():
        return mock_scoring_service
    
    from routers.scoring import get_db, get_scoring_service
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_scoring_service] = override_get_scoring_service
    
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_practice_session():
    """Sample practice session."""
    session = MagicMock()
    session.id = uuid4()
    session.question = "Explain the concept and provide examples."
    session.user_transcript = None
    session.overall_score = None
    session.delivery_score = None
    session.language_use_score = None
    session.topic_dev_score = None
    session.feedback_json = None
    return session


@pytest.fixture
def sample_scoring_result():
    """Sample scoring result."""
    return ScoringResult(
        overall_score=3,
        delivery=ScoringDetail(
            score=3,
            feedback="Good clarity and pacing."
        ),
        language_use=ScoringDetail(
            score=4,
            feedback="Excellent grammar and vocabulary."
        ),
        topic_development=ScoringDetail(
            score=3,
            feedback="Covered main points well."
        ),
        improvement_tips=[
            "Work on pronunciation",
            "Add more examples",
            "Improve transitions"
        ]
    )


def test_evaluate_response_success(client_with_mocks, mock_db_session, mock_scoring_service, sample_practice_session, sample_scoring_result):
    """Test successful response evaluation."""
    # Setup mocks
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_practice_session
    mock_scoring_service.evaluate_response = AsyncMock(return_value=sample_scoring_result)
    
    # Request data
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "transcript": "The reading passage discusses cognitive dissonance...",
        "reading_text": "Cognitive dissonance is a psychological phenomenon...",
        "lecture_script": "Let me give you some examples..."
    }
    
    # Make request
    response = client_with_mocks.post("/api/scoring/evaluate", json=request_data)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["overall_score"] == 3
    assert data["delivery"]["score"] == 3
    assert data["language_use"]["score"] == 4
    assert data["topic_development"]["score"] == 3
    assert len(data["improvement_tips"]) == 3


def test_evaluate_response_invalid_problem_id(client_with_mocks):
    """Test evaluation with invalid problem_id format."""
    request_data = {
        "problem_id": "invalid-uuid",
        "transcript": "Some transcript",
        "reading_text": "Some reading",
        "lecture_script": "Some lecture"
    }
    
    response = client_with_mocks.post("/api/scoring/evaluate", json=request_data)
    
    assert response.status_code == 400
    assert "Invalid problem_id format" in response.json()["detail"]


def test_evaluate_response_session_not_found(client_with_mocks, mock_db_session):
    """Test evaluation with non-existent practice session."""
    # Setup mock to return None (session not found)
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    request_data = {
        "problem_id": str(uuid4()),
        "transcript": "Some transcript",
        "reading_text": "Some reading",
        "lecture_script": "Some lecture"
    }
    
    response = client_with_mocks.post("/api/scoring/evaluate", json=request_data)
    
    assert response.status_code == 404
    assert "Practice session not found" in response.json()["detail"]


def test_evaluate_response_empty_transcript(client_with_mocks, sample_practice_session):
    """Test evaluation with empty transcript."""
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "transcript": "",
        "reading_text": "Some reading",
        "lecture_script": "Some lecture"
    }
    
    response = client_with_mocks.post("/api/scoring/evaluate", json=request_data)
    
    # Should fail validation
    assert response.status_code == 422


def test_evaluate_response_scoring_error(client_with_mocks, mock_db_session, mock_scoring_service, sample_practice_session):
    """Test evaluation with scoring error."""
    # Setup mocks
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_practice_session
    mock_scoring_service.evaluate_response = AsyncMock(side_effect=ScoringError("Scoring failed"))
    
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "transcript": "Some transcript",
        "reading_text": "Some reading",
        "lecture_script": "Some lecture"
    }
    
    response = client_with_mocks.post("/api/scoring/evaluate", json=request_data)
    
    assert response.status_code == 400
    assert "Scoring failed" in response.json()["detail"]


def test_evaluate_response_external_api_error(client_with_mocks, mock_db_session, mock_scoring_service, sample_practice_session):
    """Test evaluation with external API error."""
    # Setup mocks
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_practice_session
    mock_scoring_service.evaluate_response = AsyncMock(
        side_effect=ExternalAPIError("OpenAI", "Rate limit exceeded")
    )
    
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "transcript": "Some transcript",
        "reading_text": "Some reading",
        "lecture_script": "Some lecture"
    }
    
    response = client_with_mocks.post("/api/scoring/evaluate", json=request_data)
    
    assert response.status_code == 503
    assert "採点処理に失敗しました" in response.json()["detail"]


def test_evaluate_response_saves_to_database(client_with_mocks, mock_db_session, mock_scoring_service, sample_practice_session, sample_scoring_result):
    """Test that evaluation results are saved to database."""
    # Setup mocks
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_practice_session
    mock_scoring_service.evaluate_response = AsyncMock(return_value=sample_scoring_result)
    
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "transcript": "Test transcript",
        "reading_text": "Test reading",
        "lecture_script": "Test lecture"
    }
    
    response = client_with_mocks.post("/api/scoring/evaluate", json=request_data)
    
    # Verify database updates
    assert response.status_code == 200
    assert sample_practice_session.user_transcript == "Test transcript"
    assert sample_practice_session.overall_score == 3
    assert sample_practice_session.delivery_score == 3
    assert sample_practice_session.language_use_score == 4
    assert sample_practice_session.topic_dev_score == 3
    assert sample_practice_session.feedback_json is not None
    assert "delivery_feedback" in sample_practice_session.feedback_json
    assert "improvement_tips" in sample_practice_session.feedback_json
    mock_db_session.commit.assert_called_once()


def test_evaluate_response_validates_scores_in_range(client_with_mocks, mock_db_session, mock_scoring_service, sample_practice_session, sample_scoring_result):
    """Test that response includes scores in valid range (0-4)."""
    # Setup mocks
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_practice_session
    mock_scoring_service.evaluate_response = AsyncMock(return_value=sample_scoring_result)
    
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "transcript": "Test transcript",
        "reading_text": "Test reading",
        "lecture_script": "Test lecture"
    }
    
    response = client_with_mocks.post("/api/scoring/evaluate", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all scores are in range
    assert 0 <= data["overall_score"] <= 4
    assert 0 <= data["delivery"]["score"] <= 4
    assert 0 <= data["language_use"]["score"] <= 4
    assert 0 <= data["topic_development"]["score"] <= 4


# Model Answer Generation Tests

@pytest.fixture
def sample_model_answer():
    """Sample model answer result."""
    from services.scoring_service import ModelAnswer, HighlightedPhrase
    return ModelAnswer(
        model_answer="The reading passage introduces the concept of cognitive dissonance. The lecture provides examples showing how this affects behavior.",
        highlighted_phrases=[
            HighlightedPhrase(
                text="The reading passage introduces",
                category="transition",
                useful_for_writing=True
            ),
            HighlightedPhrase(
                text="For instance",
                category="example",
                useful_for_writing=True
            ),
            HighlightedPhrase(
                text="This demonstrates",
                category="conclusion",
                useful_for_writing=False
            )
        ]
    )


def test_generate_model_answer_success(client_with_mocks, mock_db_session, mock_scoring_service, sample_practice_session, sample_model_answer):
    """Test successful model answer generation."""
    # Setup mocks
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_practice_session
    mock_scoring_service.generate_model_answer = AsyncMock(return_value=sample_model_answer)
    
    # Request data
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "reading_text": "Cognitive dissonance is a psychological phenomenon...",
        "lecture_script": "Let me give you some examples...",
        "question": "Explain the concept and provide examples."
    }
    
    # Make request
    response = client_with_mocks.post("/api/scoring/model-answer/generate", json=request_data)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "model_answer" in data
    assert len(data["model_answer"]) > 0
    assert "highlighted_phrases" in data
    assert len(data["highlighted_phrases"]) == 3
    assert data["highlighted_phrases"][0]["text"] == "The reading passage introduces"
    assert data["highlighted_phrases"][0]["category"] == "transition"
    assert data["highlighted_phrases"][0]["useful_for_writing"] is True
    assert data["highlighted_phrases"][1]["category"] == "example"
    assert data["highlighted_phrases"][2]["category"] == "conclusion"


def test_generate_model_answer_invalid_problem_id(client_with_mocks):
    """Test model answer generation with invalid problem_id format."""
    request_data = {
        "problem_id": "invalid-uuid",
        "reading_text": "Some reading",
        "lecture_script": "Some lecture",
        "question": "Some question"
    }
    
    response = client_with_mocks.post("/api/scoring/model-answer/generate", json=request_data)
    
    assert response.status_code == 400
    assert "Invalid problem_id format" in response.json()["detail"]


def test_generate_model_answer_session_not_found(client_with_mocks, mock_db_session):
    """Test model answer generation with non-existent practice session."""
    # Setup mock to return None (session not found)
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    request_data = {
        "problem_id": str(uuid4()),
        "reading_text": "Some reading",
        "lecture_script": "Some lecture",
        "question": "Some question"
    }
    
    response = client_with_mocks.post("/api/scoring/model-answer/generate", json=request_data)
    
    assert response.status_code == 404
    assert "Practice session not found" in response.json()["detail"]


def test_generate_model_answer_empty_reading(client_with_mocks):
    """Test model answer generation with empty reading text."""
    request_data = {
        "problem_id": str(uuid4()),
        "reading_text": "",
        "lecture_script": "Some lecture",
        "question": "Some question"
    }
    
    response = client_with_mocks.post("/api/scoring/model-answer/generate", json=request_data)
    
    # Should fail validation
    assert response.status_code == 422


def test_generate_model_answer_scoring_error(client_with_mocks, mock_db_session, mock_scoring_service, sample_practice_session):
    """Test model answer generation with scoring error."""
    # Setup mocks
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_practice_session
    mock_scoring_service.generate_model_answer = AsyncMock(side_effect=ScoringError("Generation failed"))
    
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "reading_text": "Some reading",
        "lecture_script": "Some lecture",
        "question": "Some question"
    }
    
    response = client_with_mocks.post("/api/scoring/model-answer/generate", json=request_data)
    
    assert response.status_code == 400
    assert "Generation failed" in response.json()["detail"]


def test_generate_model_answer_external_api_error(client_with_mocks, mock_db_session, mock_scoring_service, sample_practice_session):
    """Test model answer generation with external API error."""
    # Setup mocks
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_practice_session
    mock_scoring_service.generate_model_answer = AsyncMock(
        side_effect=ExternalAPIError("OpenAI", "Rate limit exceeded")
    )
    
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "reading_text": "Some reading",
        "lecture_script": "Some lecture",
        "question": "Some question"
    }
    
    response = client_with_mocks.post("/api/scoring/model-answer/generate", json=request_data)
    
    assert response.status_code == 503
    assert "模範解答の生成に失敗しました" in response.json()["detail"]


def test_generate_model_answer_saves_to_database(client_with_mocks, mock_db_session, mock_scoring_service, sample_practice_session, sample_model_answer):
    """Test that model answer is saved to database."""
    # Setup mocks
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_practice_session
    mock_scoring_service.generate_model_answer = AsyncMock(return_value=sample_model_answer)
    
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "reading_text": "Test reading",
        "lecture_script": "Test lecture",
        "question": "Test question"
    }
    
    response = client_with_mocks.post("/api/scoring/model-answer/generate", json=request_data)
    
    # Verify database updates
    assert response.status_code == 200
    assert sample_practice_session.model_answer == sample_model_answer.model_answer
    mock_db_session.commit.assert_called_once()


def test_generate_model_answer_validates_phrase_categories(client_with_mocks, mock_db_session, mock_scoring_service, sample_practice_session, sample_model_answer):
    """Test that response includes valid phrase categories."""
    # Setup mocks
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_practice_session
    mock_scoring_service.generate_model_answer = AsyncMock(return_value=sample_model_answer)
    
    request_data = {
        "problem_id": str(sample_practice_session.id),
        "reading_text": "Test reading",
        "lecture_script": "Test lecture",
        "question": "Test question"
    }
    
    response = client_with_mocks.post("/api/scoring/model-answer/generate", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all categories are valid
    valid_categories = ["transition", "example", "conclusion"]
    for phrase in data["highlighted_phrases"]:
        assert phrase["category"] in valid_categories
        assert isinstance(phrase["useful_for_writing"], bool)
