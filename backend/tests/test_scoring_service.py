"""
Unit tests for ScoringService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.scoring_service import ScoringService, ScoringResult, ScoringDetail
from exceptions import ScoringError


@pytest.fixture
def scoring_service():
    """Create a ScoringService instance for testing."""
    with patch('services.scoring_service.get_openai_client') as mock_client:
        service = ScoringService()
        service.openai_client = mock_client.return_value
        return service


@pytest.fixture
def sample_scoring_data():
    """Sample scoring data from OpenAI."""
    return {
        "delivery_score": 3,
        "delivery_feedback": "Good clarity and pacing, minor pronunciation issues.",
        "language_use_score": 4,
        "language_use_feedback": "Excellent grammar and vocabulary usage.",
        "topic_dev_score": 3,
        "topic_dev_feedback": "Covered main points but could include more detail.",
        "overall_score": 3,
        "improvement_tips": [
            "Work on pronunciation of technical terms",
            "Add more specific examples",
            "Improve transitions between ideas"
        ]
    }


@pytest.mark.asyncio
async def test_evaluate_response_success(scoring_service, sample_scoring_data):
    """Test successful response evaluation."""
    # Mock OpenAI client response
    scoring_service.openai_client.score_response = AsyncMock(return_value=sample_scoring_data)
    
    # Test data
    transcript = "The reading passage discusses the concept of cognitive dissonance..."
    reading_text = "Cognitive dissonance is a psychological phenomenon..."
    lecture_script = "Now, let me give you some examples of cognitive dissonance..."
    question = "Explain the concept and provide examples from the lecture."
    
    # Call service
    result = await scoring_service.evaluate_response(
        transcript=transcript,
        reading_text=reading_text,
        lecture_script=lecture_script,
        question=question
    )
    
    # Assertions
    assert isinstance(result, ScoringResult)
    assert result.overall_score == 3
    assert result.delivery.score == 3
    assert result.language_use.score == 4
    assert result.topic_development.score == 3
    assert len(result.improvement_tips) == 3
    assert "pronunciation" in result.improvement_tips[0].lower()


@pytest.mark.asyncio
async def test_evaluate_response_empty_transcript(scoring_service):
    """Test evaluation with empty transcript."""
    with pytest.raises(ScoringError, match="Transcript cannot be empty"):
        await scoring_service.evaluate_response(
            transcript="",
            reading_text="Some reading text",
            lecture_script="Some lecture script",
            question="Some question"
        )


@pytest.mark.asyncio
async def test_evaluate_response_empty_reading(scoring_service):
    """Test evaluation with empty reading text."""
    with pytest.raises(ScoringError, match="Reading text cannot be empty"):
        await scoring_service.evaluate_response(
            transcript="Some transcript",
            reading_text="",
            lecture_script="Some lecture script",
            question="Some question"
        )


@pytest.mark.asyncio
async def test_evaluate_response_empty_lecture(scoring_service):
    """Test evaluation with empty lecture script."""
    with pytest.raises(ScoringError, match="Lecture script cannot be empty"):
        await scoring_service.evaluate_response(
            transcript="Some transcript",
            reading_text="Some reading text",
            lecture_script="",
            question="Some question"
        )


@pytest.mark.asyncio
async def test_evaluate_response_empty_question(scoring_service):
    """Test evaluation with empty question."""
    with pytest.raises(ScoringError, match="Question cannot be empty"):
        await scoring_service.evaluate_response(
            transcript="Some transcript",
            reading_text="Some reading text",
            lecture_script="Some lecture script",
            question=""
        )


def test_parse_scoring_data_success(scoring_service, sample_scoring_data):
    """Test successful parsing of scoring data."""
    result = scoring_service._parse_scoring_data(sample_scoring_data)
    
    assert result.overall_score == 3
    assert result.delivery.score == 3
    assert result.delivery.feedback == "Good clarity and pacing, minor pronunciation issues."
    assert result.language_use.score == 4
    assert result.topic_development.score == 3
    assert len(result.improvement_tips) == 3


def test_parse_scoring_data_missing_score(scoring_service):
    """Test parsing with missing score field."""
    data = {
        "delivery_feedback": "Good",
        "language_use_score": 3,
        "language_use_feedback": "Good",
        "topic_dev_score": 3,
        "topic_dev_feedback": "Good",
        "overall_score": 3,
        "improvement_tips": ["tip1"]
    }
    
    with pytest.raises(ScoringError, match="Missing required field: delivery_score"):
        scoring_service._parse_scoring_data(data)


def test_parse_scoring_data_missing_feedback(scoring_service):
    """Test parsing with missing feedback field."""
    data = {
        "delivery_score": 3,
        "delivery_feedback": "",
        "language_use_score": 3,
        "language_use_feedback": "Good",
        "topic_dev_score": 3,
        "topic_dev_feedback": "Good",
        "overall_score": 3,
        "improvement_tips": ["tip1"]
    }
    
    with pytest.raises(ScoringError, match="Missing delivery feedback"):
        scoring_service._parse_scoring_data(data)


def test_parse_scoring_data_missing_tips(scoring_service):
    """Test parsing with missing improvement tips."""
    data = {
        "delivery_score": 3,
        "delivery_feedback": "Good",
        "language_use_score": 3,
        "language_use_feedback": "Good",
        "topic_dev_score": 3,
        "topic_dev_feedback": "Good",
        "overall_score": 3,
        "improvement_tips": []
    }
    
    with pytest.raises(ScoringError, match="At least one improvement tip is required"):
        scoring_service._parse_scoring_data(data)


def test_validate_score_success(scoring_service):
    """Test successful score validation."""
    assert scoring_service._validate_score(0, "test") == 0
    assert scoring_service._validate_score(2, "test") == 2
    assert scoring_service._validate_score(4, "test") == 4


def test_validate_score_float_conversion(scoring_service):
    """Test score validation with float input."""
    assert scoring_service._validate_score(3.0, "test") == 3
    assert scoring_service._validate_score(2.9, "test") == 2


def test_validate_score_out_of_range(scoring_service):
    """Test score validation with out of range values."""
    with pytest.raises(ScoringError, match="must be between 0 and 4"):
        scoring_service._validate_score(-1, "test")
    
    with pytest.raises(ScoringError, match="must be between 0 and 4"):
        scoring_service._validate_score(5, "test")


def test_validate_score_invalid_type(scoring_service):
    """Test score validation with invalid type."""
    with pytest.raises(ScoringError, match="Invalid score type"):
        scoring_service._validate_score("3", "test")


def test_validate_score_none(scoring_service):
    """Test score validation with None."""
    with pytest.raises(ScoringError, match="Missing required field"):
        scoring_service._validate_score(None, "test")


@pytest.mark.asyncio
async def test_evaluate_response_with_float_scores(scoring_service):
    """Test evaluation with float scores from OpenAI."""
    # Mock OpenAI client response with float scores
    scoring_data = {
        "delivery_score": 3.0,
        "delivery_feedback": "Good delivery",
        "language_use_score": 4.0,
        "language_use_feedback": "Excellent language",
        "topic_dev_score": 3.0,
        "topic_dev_feedback": "Good content",
        "overall_score": 3.0,
        "improvement_tips": ["Practice more"]
    }
    scoring_service.openai_client.score_response = AsyncMock(return_value=scoring_data)
    
    result = await scoring_service.evaluate_response(
        transcript="Test transcript",
        reading_text="Test reading",
        lecture_script="Test lecture",
        question="Test question"
    )
    
    # Should convert floats to ints
    assert result.overall_score == 3
    assert result.delivery.score == 3
    assert result.language_use.score == 4
    assert result.topic_development.score == 3


# Model Answer Generation Tests

@pytest.fixture
def sample_model_answer_data():
    """Sample model answer data from OpenAI."""
    return {
        "model_answer": "The reading passage introduces the concept of cognitive dissonance, which occurs when people hold contradictory beliefs. The lecture provides concrete examples of this phenomenon. For instance, the professor describes a study where participants experienced dissonance after making difficult decisions. This demonstrates how cognitive dissonance affects everyday behavior.",
        "highlighted_phrases": [
            {
                "text": "The reading passage introduces",
                "category": "transition",
                "useful_for_writing": True
            },
            {
                "text": "For instance",
                "category": "example",
                "useful_for_writing": True
            },
            {
                "text": "This demonstrates how",
                "category": "conclusion",
                "useful_for_writing": True
            }
        ]
    }


@pytest.mark.asyncio
async def test_generate_model_answer_success(scoring_service, sample_model_answer_data):
    """Test successful model answer generation."""
    # Mock OpenAI client response
    scoring_service.openai_client.generate_model_answer = AsyncMock(return_value=sample_model_answer_data)
    
    # Test data
    reading_text = "Cognitive dissonance is a psychological phenomenon..."
    lecture_script = "Now, let me give you some examples of cognitive dissonance..."
    question = "Explain the concept and provide examples from the lecture."
    
    # Call service
    result = await scoring_service.generate_model_answer(
        reading_text=reading_text,
        lecture_script=lecture_script,
        question=question
    )
    
    # Assertions
    assert result.model_answer == sample_model_answer_data["model_answer"]
    assert len(result.highlighted_phrases) == 3
    assert result.highlighted_phrases[0].text == "The reading passage introduces"
    assert result.highlighted_phrases[0].category == "transition"
    assert result.highlighted_phrases[0].useful_for_writing is True
    assert result.highlighted_phrases[1].category == "example"
    assert result.highlighted_phrases[2].category == "conclusion"


@pytest.mark.asyncio
async def test_generate_model_answer_empty_reading(scoring_service):
    """Test model answer generation with empty reading text."""
    with pytest.raises(ScoringError, match="Reading text cannot be empty"):
        await scoring_service.generate_model_answer(
            reading_text="",
            lecture_script="Some lecture script",
            question="Some question"
        )


@pytest.mark.asyncio
async def test_generate_model_answer_empty_lecture(scoring_service):
    """Test model answer generation with empty lecture script."""
    with pytest.raises(ScoringError, match="Lecture script cannot be empty"):
        await scoring_service.generate_model_answer(
            reading_text="Some reading text",
            lecture_script="",
            question="Some question"
        )


@pytest.mark.asyncio
async def test_generate_model_answer_empty_question(scoring_service):
    """Test model answer generation with empty question."""
    with pytest.raises(ScoringError, match="Question cannot be empty"):
        await scoring_service.generate_model_answer(
            reading_text="Some reading text",
            lecture_script="Some lecture script",
            question=""
        )


def test_parse_model_answer_data_success(scoring_service, sample_model_answer_data):
    """Test successful parsing of model answer data."""
    result = scoring_service._parse_model_answer_data(sample_model_answer_data)
    
    assert result.model_answer == sample_model_answer_data["model_answer"]
    assert len(result.highlighted_phrases) == 3
    assert result.highlighted_phrases[0].text == "The reading passage introduces"
    assert result.highlighted_phrases[0].category == "transition"
    assert result.highlighted_phrases[0].useful_for_writing is True


def test_parse_model_answer_data_missing_answer(scoring_service):
    """Test parsing with missing model answer text."""
    data = {
        "model_answer": "",
        "highlighted_phrases": []
    }
    
    with pytest.raises(ScoringError, match="Missing model answer text"):
        scoring_service._parse_model_answer_data(data)


def test_parse_model_answer_data_no_phrases(scoring_service):
    """Test parsing with no highlighted phrases (should succeed)."""
    data = {
        "model_answer": "This is a model answer.",
        "highlighted_phrases": []
    }
    
    result = scoring_service._parse_model_answer_data(data)
    assert result.model_answer == "This is a model answer."
    assert len(result.highlighted_phrases) == 0


def test_parse_model_answer_data_invalid_category(scoring_service):
    """Test parsing with invalid category (should default to 'example')."""
    data = {
        "model_answer": "This is a model answer.",
        "highlighted_phrases": [
            {
                "text": "Some phrase",
                "category": "invalid_category",
                "useful_for_writing": True
            }
        ]
    }
    
    result = scoring_service._parse_model_answer_data(data)
    assert len(result.highlighted_phrases) == 1
    assert result.highlighted_phrases[0].category == "example"


def test_parse_model_answer_data_missing_phrase_fields(scoring_service):
    """Test parsing with missing phrase fields (should skip invalid phrases)."""
    data = {
        "model_answer": "This is a model answer.",
        "highlighted_phrases": [
            {
                "text": "Valid phrase",
                "category": "transition",
                "useful_for_writing": True
            },
            {
                "text": "",  # Empty text, should be skipped
                "category": "example",
                "useful_for_writing": False
            },
            {
                "category": "conclusion",  # Missing text, should be skipped
                "useful_for_writing": True
            }
        ]
    }
    
    result = scoring_service._parse_model_answer_data(data)
    assert len(result.highlighted_phrases) == 1
    assert result.highlighted_phrases[0].text == "Valid phrase"
