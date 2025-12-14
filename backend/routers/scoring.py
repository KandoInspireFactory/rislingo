"""
Scoring router for TOEFL Speaking Master API.
Handles scoring of user responses and model answer generation.
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import PracticeSession
from services.scoring_service import get_scoring_service, ScoringService
from exceptions import ScoringError, ExternalAPIError
from utils.audio_cleanup import schedule_audio_cleanup


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/scoring",
    tags=["scoring"]
)


# Request/Response models
class Task1ScoringRequest(BaseModel):
    """Request model for Task 1 scoring evaluation."""
    problem_id: str = Field(..., description="UUID of the practice session")
    transcript: str = Field(..., min_length=1, description="Transcribed user response")
    question: str = Field(..., min_length=1, description="The question asked")


class Task1ScoringResponse(BaseModel):
    """Response model for Task 1 scoring evaluation."""
    overall_score: int = Field(..., ge=0, le=4, description="Overall score from 0 to 4")
    delivery_feedback: str = Field(..., description="Feedback on delivery")
    language_use_feedback: str = Field(..., description="Feedback on language use")
    topic_dev_feedback: str = Field(..., description="Feedback on topic development")
    improvement_tips: List[str] = Field(..., description="List of improvement suggestions")
    strengths: List[str] = Field(..., description="List of strengths identified")
    user_transcript: str = Field(..., description="User's transcribed response")


class Task1ModelAnswerRequest(BaseModel):
    """Request model for Task 1 model answer generation."""
    problem_id: str = Field(..., description="UUID of the practice session")
    question: str = Field(..., min_length=1, description="The question asked")


class Task2ModelAnswerRequest(BaseModel):
    """Request model for Task 2 model answer generation."""
    problem_id: str = Field(..., description="UUID of the practice session")
    announcement_text: str = Field(..., min_length=1, description="University announcement text")
    conversation_script: str = Field(..., min_length=1, description="Student conversation script")
    question: str = Field(..., min_length=1, description="The question asked")


class Task1HighlightedPhraseResponse(BaseModel):
    """Response model for a Task 1 highlighted phrase."""
    text: str = Field(..., description="The phrase text")
    category: str = Field(..., description="Category: introduction, transition, example, or conclusion")
    explanation: str = Field(..., description="Explanation of why this phrase is effective")


class Task1ModelAnswerResponse(BaseModel):
    """Response model for Task 1 model answer generation."""
    model_answer: str = Field(..., description="The complete model answer text")
    highlighted_phrases: List[Task1HighlightedPhraseResponse] = Field(..., description="List of highlighted phrases with explanations")


class ScoringDetailResponse(BaseModel):
    """Detailed scoring information for a single criterion."""
    score: int = Field(..., ge=0, le=4, description="Score from 0 to 4")
    feedback: str = Field(..., description="Detailed feedback for this criterion")


class ScoringRequest(BaseModel):
    """Request model for scoring evaluation."""
    problem_id: str = Field(..., description="UUID of the practice session")
    transcript: str = Field(..., min_length=1, description="Transcribed user response")
    reading_text: Optional[str] = Field(None, description="Original reading passage (optional for Task4)")
    lecture_script: str = Field(..., min_length=1, description="Original lecture script")


class ScoringResponse(BaseModel):
    """Response model for scoring evaluation."""
    overall_score: int = Field(..., ge=0, le=4, description="Overall score from 0 to 4")
    delivery: ScoringDetailResponse
    language_use: ScoringDetailResponse
    topic_development: ScoringDetailResponse
    improvement_tips: List[str] = Field(..., description="List of improvement suggestions")
    user_transcript: str = Field(..., description="User's transcribed response")


class HighlightedPhraseResponse(BaseModel):
    """Response model for a highlighted phrase."""
    text: str = Field(..., description="The phrase text")
    category: str = Field(..., description="Category: transition, example, or conclusion")
    useful_for_writing: bool = Field(..., description="Whether this phrase is useful for TOEFL Writing")


class ModelAnswerRequest(BaseModel):
    """Request model for model answer generation."""
    problem_id: str = Field(..., description="UUID of the practice session")
    reading_text: Optional[str] = Field(None, description="Original reading passage (optional for Task4)")
    lecture_script: str = Field(..., min_length=1, description="Original lecture script")
    question: str = Field(..., min_length=1, description="The question asked")


class ModelAnswerResponse(BaseModel):
    """Response model for model answer generation."""
    model_answer: str = Field(..., description="The complete model answer text")
    highlighted_phrases: List[HighlightedPhraseResponse] = Field(..., description="List of highlighted phrases with categories")


class AIReviewRequest(BaseModel):
    """Request model for AI review generation."""
    task_type: str = Field(..., description="Task type: task1, task2, task3, or task4")
    problem_id: str = Field(..., description="UUID of the practice session")
    user_transcript: str = Field(..., min_length=1, description="User's transcribed response")
    question: str = Field(..., min_length=1, description="The question asked")
    reading_text: Optional[str] = Field(None, description="Reading passage (for task2/task3)")
    lecture_script: Optional[str] = Field(None, description="Lecture script (for task2/task3/task4)")
    announcement_text: Optional[str] = Field(None, description="Announcement text (for task2)")
    conversation_script: Optional[str] = Field(None, description="Conversation script (for task2)")


class AIReviewResponse(BaseModel):
    """Response model for AI review generation."""
    strengths: List[str] = Field(..., description="List of strengths in the user's response")
    improvements: List[str] = Field(..., description="List of areas for improvement")
    specific_suggestions: str = Field(..., description="Specific suggestions based on user's response")
    score_improvement_tips: str = Field(..., description="Tips for improving the score")
    improved_response: str = Field(..., description="Improved version of user's response")


@router.post("/evaluate-task1", response_model=Task1ScoringResponse)
async def evaluate_task1_response(
    request: Task1ScoringRequest,
    db: Session = Depends(get_db),
    scoring_service: ScoringService = Depends(get_scoring_service)
):
    """
    Evaluate a TOEFL Speaking Task 1 (Independent) response using AI scoring.
    
    Scores the response based on overall performance using the official TOEFL criteria:
    0点: 全く話していない
    1点: ほとんど話していない
    2点: 英語の間違いが散見しつつ、テンポと構成がまずく問に答えきれていない
    3点: 英語の間違いは散見しつつも、テンポと構成よく問に答えきれている
    4点: 英語の表現がよく、構成も回答もよい
    
    Args:
        request: Task 1 scoring request with transcript and question
        db: Database session
        scoring_service: Scoring service instance
        
    Returns:
        Task1ScoringResponse with score and feedback
        
    Raises:
        HTTPException: If scoring fails
    """
    try:
        logger.info(f"Received Task 1 scoring request for problem_id: {request.problem_id}")
        
        # Validate problem_id is a valid UUID
        try:
            problem_uuid = UUID(request.problem_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid problem_id format")
        
        # Verify the practice session exists
        session = db.query(PracticeSession).filter(PracticeSession.id == problem_uuid).first()
        if not session:
            raise HTTPException(status_code=404, detail="Practice session not found")
        
        # Evaluate the Task 1 response
        result = await scoring_service.evaluate_task1_response(
            transcript=request.transcript,
            question=request.question
        )
        
        # Update the practice session with scoring results
        session.user_transcript = request.transcript
        session.overall_score = result.get("overall_score", 0)
        session.feedback_json = {
            "delivery_feedback": result.get("delivery_feedback", ""),
            "language_use_feedback": result.get("language_use_feedback", ""),
            "topic_dev_feedback": result.get("topic_dev_feedback", ""),
            "improvement_tips": result.get("improvement_tips", []),
            "strengths": result.get("strengths", [])
        }
        
        db.commit()
        logger.info(f"Task 1 scoring completed and saved for problem_id: {request.problem_id}")
        
        # Clean up audio file after scoring
        schedule_audio_cleanup(request.problem_id)
        
        # Return scoring response
        return Task1ScoringResponse(
            overall_score=result.get("overall_score", 0),
            delivery_feedback=result.get("delivery_feedback", ""),
            language_use_feedback=result.get("language_use_feedback", ""),
            topic_dev_feedback=result.get("topic_dev_feedback", ""),
            improvement_tips=result.get("improvement_tips", []),
            strengths=result.get("strengths", []),
            user_transcript=request.transcript
        )
        
    except HTTPException:
        raise
    except ScoringError as e:
        logger.error(f"Task 1 scoring error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ExternalAPIError as e:
        logger.error(f"External API error: {e}")
        raise HTTPException(status_code=503, detail=f"採点処理に失敗しました。もう一度お試しください。")
    except Exception as e:
        logger.error(f"Unexpected error in Task 1 scoring endpoint: {e}")
        raise HTTPException(status_code=500, detail="採点処理中にエラーが発生しました。")


@router.post("/model-answer/generate-task2", response_model=ModelAnswerResponse)
async def generate_task2_model_answer(
    request: Task2ModelAnswerRequest,
    db: Session = Depends(get_db),
    scoring_service: ScoringService = Depends(get_scoring_service)
):
    """
    Generate a model answer for a TOEFL Speaking Task 2 (Integrated) question.
    
    The model answer demonstrates excellent structure and language use for integrated speaking,
    with highlighted phrases showing key patterns (transitions, summaries, conclusions).
    
    Args:
        request: Task 2 model answer request with announcement, conversation, and question
        db: Database session
        scoring_service: Scoring service instance
        
    Returns:
        ModelAnswerResponse with answer text and highlighted phrases
        
    Raises:
        HTTPException: If model answer generation fails
    """
    try:
        logger.info(f"Received Task 2 model answer request for problem_id: {request.problem_id}")
        
        # Validate problem_id is a valid UUID
        try:
            problem_uuid = UUID(request.problem_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid problem_id format")
        
        # Verify the practice session exists
        session = db.query(PracticeSession).filter(PracticeSession.id == problem_uuid).first()
        if not session:
            raise HTTPException(status_code=404, detail="Practice session not found")
        
        # Generate Task 2 model answer
        result = await scoring_service.generate_task2_model_answer(
            announcement_text=request.announcement_text,
            conversation_script=request.conversation_script,
            question=request.question
        )
        
        # Update the practice session with model answer
        session.model_answer = result.get("model_answer", "")
        db.commit()
        logger.info(f"Task 2 model answer generated and saved for problem_id: {request.problem_id}")
        
        # Return model answer response
        highlighted_phrases = []
        for phrase in result.get("highlighted_phrases", []):
            highlighted_phrases.append(
                HighlightedPhraseResponse(
                    text=phrase.get("text", ""),
                    category=phrase.get("category", ""),
                    useful_for_writing=phrase.get("useful_for_writing", False)
                )
            )
        
        return ModelAnswerResponse(
            model_answer=result.get("model_answer", ""),
            highlighted_phrases=highlighted_phrases
        )
        
    except HTTPException:
        raise
    except ScoringError as e:
        logger.error(f"Task 2 model answer generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ExternalAPIError as e:
        logger.error(f"External API error: {e}")
        raise HTTPException(status_code=503, detail=f"模範解答の生成に失敗しました。もう一度お試しください。")
    except Exception as e:
        logger.error(f"Unexpected error in Task 2 model answer endpoint: {e}")
        raise HTTPException(status_code=500, detail="模範解答生成中にエラーが発生しました。")


@router.post("/model-answer/generate-task1", response_model=Task1ModelAnswerResponse)
async def generate_task1_model_answer(
    request: Task1ModelAnswerRequest,
    db: Session = Depends(get_db),
    scoring_service: ScoringService = Depends(get_scoring_service)
):
    """
    Generate a model answer for a TOEFL Speaking Task 1 (Independent) question.
    
    The model answer demonstrates excellent structure and language use for independent speaking,
    with highlighted phrases showing key patterns (introduction, transitions, examples, conclusions).
    
    Args:
        request: Task 1 model answer request with question
        db: Database session
        scoring_service: Scoring service instance
        
    Returns:
        Task1ModelAnswerResponse with answer text and highlighted phrases
        
    Raises:
        HTTPException: If model answer generation fails
    """
    try:
        logger.info(f"Received Task 1 model answer request for problem_id: {request.problem_id}")
        
        # Validate problem_id is a valid UUID
        try:
            problem_uuid = UUID(request.problem_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid problem_id format")
        
        # Verify the practice session exists
        session = db.query(PracticeSession).filter(PracticeSession.id == problem_uuid).first()
        if not session:
            raise HTTPException(status_code=404, detail="Practice session not found")
        
        # Generate Task 1 model answer
        result = await scoring_service.generate_task1_model_answer(
            question=request.question
        )
        
        # Update the practice session with model answer
        session.model_answer = result.get("model_answer", "")
        db.commit()
        logger.info(f"Task 1 model answer generated and saved for problem_id: {request.problem_id}")
        
        # Return model answer response
        highlighted_phrases = []
        for phrase in result.get("highlighted_phrases", []):
            highlighted_phrases.append(
                Task1HighlightedPhraseResponse(
                    text=phrase.get("text", ""),
                    category=phrase.get("category", ""),
                    explanation=phrase.get("explanation", "")
                )
            )
        
        return Task1ModelAnswerResponse(
            model_answer=result.get("model_answer", ""),
            highlighted_phrases=highlighted_phrases
        )
        
    except HTTPException:
        raise
    except ScoringError as e:
        logger.error(f"Task 1 model answer generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ExternalAPIError as e:
        logger.error(f"External API error: {e}")
        raise HTTPException(status_code=503, detail=f"模範解答の生成に失敗しました。もう一度お試しください。")
    except Exception as e:
        logger.error(f"Unexpected error in Task 1 model answer endpoint: {e}")
        raise HTTPException(status_code=500, detail="模範解答生成中にエラーが発生しました。")


@router.post("/evaluate", response_model=ScoringResponse)
async def evaluate_response(
    request: ScoringRequest,
    db: Session = Depends(get_db),
    scoring_service: ScoringService = Depends(get_scoring_service)
):
    """
    Evaluate a TOEFL Speaking response using AI scoring.
    
    Scores the response based on three criteria:
    - Delivery: Clarity, fluency, pronunciation, pacing
    - Language Use: Grammar, vocabulary, sentence structure
    - Topic Development: Content accuracy, completeness, coherence
    
    Each criterion is scored on a 0-4 scale according to TOEFL rubrics.
    
    Args:
        request: Scoring request with transcript and problem context
        db: Database session
        scoring_service: Scoring service instance
        
    Returns:
        ScoringResponse with scores and feedback
        
    Raises:
        HTTPException: If scoring fails
    """
    try:
        logger.info(f"Received scoring request for problem_id: {request.problem_id}")
        
        # Validate problem_id is a valid UUID
        try:
            problem_uuid = UUID(request.problem_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid problem_id format")
        
        # Verify the practice session exists
        session = db.query(PracticeSession).filter(PracticeSession.id == problem_uuid).first()
        if not session:
            raise HTTPException(status_code=404, detail="Practice session not found")
        
        # Get the question from the session
        question = session.question
        
        # Evaluate the response
        result = await scoring_service.evaluate_response(
            transcript=request.transcript,
            reading_text=request.reading_text,
            lecture_script=request.lecture_script,
            question=question
        )
        
        # Update the practice session with scoring results
        session.user_transcript = request.transcript
        session.overall_score = result.overall_score
        session.delivery_score = result.delivery.score
        session.language_use_score = result.language_use.score
        session.topic_dev_score = result.topic_development.score
        session.feedback_json = {
            "delivery_feedback": result.delivery.feedback,
            "language_use_feedback": result.language_use.feedback,
            "topic_dev_feedback": result.topic_development.feedback,
            "improvement_tips": result.improvement_tips
        }
        
        db.commit()
        logger.info(f"Scoring completed and saved for problem_id: {request.problem_id}")
        
        # Clean up audio file after scoring (security requirement 11.3)
        schedule_audio_cleanup(request.problem_id)
        
        # Return scoring response
        return ScoringResponse(
            overall_score=result.overall_score,
            delivery=ScoringDetailResponse(
                score=result.delivery.score,
                feedback=result.delivery.feedback
            ),
            language_use=ScoringDetailResponse(
                score=result.language_use.score,
                feedback=result.language_use.feedback
            ),
            topic_development=ScoringDetailResponse(
                score=result.topic_development.score,
                feedback=result.topic_development.feedback
            ),
            improvement_tips=result.improvement_tips,
            user_transcript=request.transcript
        )
        
    except HTTPException:
        raise
    except ScoringError as e:
        logger.error(f"Scoring error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ExternalAPIError as e:
        logger.error(f"External API error: {e}")
        raise HTTPException(status_code=503, detail=f"採点処理に失敗しました。もう一度お試しください。")
    except Exception as e:
        logger.error(f"Unexpected error in scoring endpoint: {e}")
        raise HTTPException(status_code=500, detail="採点処理中にエラーが発生しました。")


@router.post("/model-answer/generate", response_model=ModelAnswerResponse)
async def generate_model_answer(
    request: ModelAnswerRequest,
    db: Session = Depends(get_db),
    scoring_service: ScoringService = Depends(get_scoring_service)
):
    """
    Generate a model answer for a TOEFL Speaking Task 3 question.
    
    The model answer demonstrates excellent structure and language use,
    with highlighted phrases showing key patterns (transitions, examples, conclusions).
    Phrases marked as useful for writing can be saved for flashcard review.
    
    Args:
        request: Model answer request with problem context
        db: Database session
        scoring_service: Scoring service instance
        
    Returns:
        ModelAnswerResponse with answer text and highlighted phrases
        
    Raises:
        HTTPException: If model answer generation fails
    """
    try:
        logger.info(f"Received model answer request for problem_id: {request.problem_id}")
        
        # Validate problem_id is a valid UUID
        try:
            problem_uuid = UUID(request.problem_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid problem_id format")
        
        # Verify the practice session exists
        session = db.query(PracticeSession).filter(PracticeSession.id == problem_uuid).first()
        if not session:
            raise HTTPException(status_code=404, detail="Practice session not found")
        
        # Generate model answer
        result = await scoring_service.generate_model_answer(
            reading_text=request.reading_text,
            lecture_script=request.lecture_script,
            question=request.question
        )
        
        # Update the practice session with model answer
        session.model_answer = result.model_answer
        db.commit()
        logger.info(f"Model answer generated and saved for problem_id: {request.problem_id}")
        
        # Return model answer response
        return ModelAnswerResponse(
            model_answer=result.model_answer,
            highlighted_phrases=[
                HighlightedPhraseResponse(
                    text=phrase.text,
                    category=phrase.category,
                    useful_for_writing=phrase.useful_for_writing
                )
                for phrase in result.highlighted_phrases
            ]
        )
        
    except HTTPException:
        raise
    except ScoringError as e:
        logger.error(f"Model answer generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ExternalAPIError as e:
        logger.error(f"External API error: {e}")
        raise HTTPException(status_code=503, detail=f"模範解答の生成に失敗しました。もう一度お試しください。")
    except Exception as e:
        logger.error(f"Unexpected error in model answer endpoint: {e}")
        raise HTTPException(status_code=500, detail="模範解答生成中にエラーが発生しました。")


@router.post("/ai-review", response_model=AIReviewResponse)
async def generate_ai_review(
    request: AIReviewRequest,
    db: Session = Depends(get_db),
    scoring_service: ScoringService = Depends(get_scoring_service)
):
    """
    Generate AI review for user's response with personalized feedback.
    
    Provides detailed analysis of the user's response including:
    - Strengths identified in the response
    - Areas for improvement
    - Specific suggestions based on the user's actual response
    - Score improvement tips tailored to the task and user's performance
    
    Args:
        request: AI review request with user transcript and problem context
        db: Database session
        scoring_service: Scoring service instance
        
    Returns:
        AIReviewResponse with personalized feedback
        
    Raises:
        HTTPException: If AI review generation fails
    """
    try:
        logger.info(f"Received AI review request for problem_id: {request.problem_id}, task_type: {request.task_type}")
        
        # Validate problem_id is a valid UUID
        try:
            problem_uuid = UUID(request.problem_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid problem_id format")
        
        # Verify the practice session exists
        session = db.query(PracticeSession).filter(PracticeSession.id == problem_uuid).first()
        if not session:
            raise HTTPException(status_code=404, detail="Practice session not found")
        
        # Generate AI review based on task type
        result = await scoring_service.generate_ai_review(
            task_type=request.task_type,
            user_transcript=request.user_transcript,
            question=request.question,
            reading_text=request.reading_text,
            lecture_script=request.lecture_script,
            announcement_text=request.announcement_text,
            conversation_script=request.conversation_script
        )
        
        logger.info(f"AI review generated successfully for problem_id: {request.problem_id}")
        
        # Return AI review response
        return AIReviewResponse(
            strengths=result.get("strengths", []),
            improvements=result.get("improvements", []),
            specific_suggestions=result.get("specific_suggestions", ""),
            score_improvement_tips=result.get("score_improvement_tips", ""),
            improved_response=result.get("improved_response", "")
        )
        
    except HTTPException:
        raise
    except ScoringError as e:
        logger.error(f"AI review generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ExternalAPIError as e:
        logger.error(f"External API error: {e}")
        raise HTTPException(status_code=503, detail=f"AI添削の生成に失敗しました。もう一度お試しください。")
    except Exception as e:
        logger.error(f"Unexpected error in AI review endpoint: {e}")
        raise HTTPException(status_code=500, detail="AI添削生成中にエラーが発生しました。")


@router.post("/generate-speech")
async def generate_speech_audio(
    request: dict,
    scoring_service: ScoringService = Depends(get_scoring_service)
):
    """
    Generate speech audio from text using OpenAI TTS.
    
    Args:
        request: Dictionary with 'text' field containing the text to convert to speech
        scoring_service: Scoring service instance
        
    Returns:
        Audio file as streaming response
        
    Raises:
        HTTPException: If speech generation fails
    """
    try:
        text = request.get("text", "")
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        logger.info(f"Generating speech for text length: {len(text)} characters")
        
        # Generate speech using OpenAI TTS
        from services.openai_client import get_openai_client
        openai_client = get_openai_client()
        
        audio_bytes = await openai_client.generate_speech(
            text=text,
            voice="alloy",
            speed=1.0
        )
        
        logger.info(f"Speech generation completed, audio size: {len(audio_bytes)} bytes")
        
        # Return audio as streaming response
        from fastapi.responses import Response
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=improved_response.mp3",
                "Content-Length": str(len(audio_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in speech generation endpoint: {e}")
        raise HTTPException(status_code=500, detail="音声生成中にエラーが発生しました。")
