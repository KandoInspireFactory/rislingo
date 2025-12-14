"""
Problems router for TOEFL Speaking Master API.
Handles problem generation endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional
import logging
from sqlalchemy.orm import Session

from services.problem_generator import get_problem_generator
from exceptions import ProblemGenerationError, ExternalAPIError
from database import get_db
from models import PracticeSession, User
from uuid import UUID


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/problems",
    tags=["problems"]
)


# Request/Response models
class ProblemGenerateRequest(BaseModel):
    """Request model for problem generation."""
    task_type: str = Field(default="task3", description="Task type (task1, task2, task3, task4 supported)")
    topic_category: Optional[str] = Field(default=None, description="Optional specific topic category")
    user_id: str = Field(..., description="User identifier")


class ProblemGenerateResponse(BaseModel):
    """Response model for generated problem."""
    problem_id: str
    reading_text: Optional[str] = None  # Task1では不要
    lecture_audio_url: Optional[str] = None  # Task1では不要
    lecture_script: Optional[str] = None  # Task1では不要
    question: str
    topic_category: Optional[str] = None  # Task1では不要
    task_type: str
    preparation_time: Optional[int] = None  # Task1では15秒
    speaking_time: Optional[int] = None  # Task1では45秒


@router.post("/generate", response_model=ProblemGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_problem(request: ProblemGenerateRequest, db: Session = Depends(get_db)):
    """
    Generate a new TOEFL Task 3 problem.
    
    This endpoint:
    1. Selects a random academic topic (or uses provided topic)
    2. Generates reading passage, lecture script, and question using GPT-4
    3. Creates audio file for the lecture using OpenAI TTS
    4. Creates a practice session in the database
    5. Returns complete problem data
    
    Args:
        request: Problem generation request with user_id and optional topic category
        db: Database session
        
    Returns:
        Complete problem with reading, lecture audio URL, script, and question
        
    Raises:
        HTTPException: If problem generation fails
    """
    # Validate task type first (before try block)
    if request.task_type not in ["task1", "task2", "task3", "task4"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currently only task1, task2, task3, and task4 are supported"
        )
    
    try:
        logger.info(f"Received problem generation request: task_type={request.task_type}, topic={request.topic_category}, user={request.user_id}")
        
        # Verify user exists
        user = db.query(User).filter(User.user_identifier == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate problem
        problem_generator = get_problem_generator()
        problem_data = await problem_generator.generate_problem(
            task_type=request.task_type,
            topic_category=request.topic_category,
            user_identifier=request.user_id,
            db=db
        )
        
        logger.info(f"Problem generated successfully: {problem_data['problem_id']}")
        
        # Create practice session in database
        try:
            problem_uuid = UUID(problem_data["problem_id"]) 
            logger.info(f"Creating practice session with UUID: {problem_uuid}")

            # Create practice session with task-specific data
            if request.task_type == "task1":
                practice_session = PracticeSession(
                    id=problem_uuid,
                    user_id=user.id,
                    task_type=request.task_type,
                    reading_text=None,  # Task1には不要
                    lecture_script=None,  # Task1には不要
                    question=problem_data["question"]
                )
            else:  # task2, task3, task4
                practice_session = PracticeSession(
                    id=problem_uuid,
                    user_id=user.id,
                    task_type=request.task_type,
                    reading_text=problem_data.get("reading_text"),
                    lecture_script=problem_data.get("lecture_script"),
                    lecture_audio_url=problem_data.get("lecture_audio_url"),
                    question=problem_data["question"]
                )
            
            logger.info("Practice session object created, adding to database...")
            db.add(practice_session)
            logger.info("Committing to database...")
            db.commit()
            logger.info(f"✅ Practice session created in database: {problem_data['problem_id']}")
        except Exception as db_error:
            logger.error(f"❌ Failed to create practice session in database: {db_error}")
            logger.error(f"Error type: {type(db_error).__name__}")
            logger.error(f"Error details: {str(db_error)}")
            db.rollback()
            # Re-raise the exception so the user knows there's a problem
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"データベースへの保存に失敗しました。データベースが起動しているか確認してください。"
            )
        
        # Return response based on task type
        if request.task_type == "task1":
            return ProblemGenerateResponse(
                problem_id=problem_data["problem_id"],
                question=problem_data["question"],
                task_type=problem_data["task_type"],
                preparation_time=problem_data.get("preparation_time", 15),
                speaking_time=problem_data.get("speaking_time", 45)
            )
        else:
            # Task4: Academic Lecture (no reading passage, includes prep & speaking times)
            if request.task_type == "task4":
                return ProblemGenerateResponse(
                    problem_id=problem_data["problem_id"],
                    reading_text=None,
                    lecture_audio_url=problem_data.get("lecture_audio_url"),
                    lecture_script=problem_data.get("lecture_script"),
                    question=problem_data["question"],
                    topic_category=problem_data.get("topic_category"),
                    task_type=problem_data["task_type"],
                    preparation_time=problem_data.get("preparation_time", 20),
                    speaking_time=problem_data.get("speaking_time", 60)
                )
            # Task2/Task3: reading + lecture
            return ProblemGenerateResponse(
                problem_id=problem_data["problem_id"],
                reading_text=problem_data.get("reading_text"),
                lecture_audio_url=problem_data.get("lecture_audio_url"),
                lecture_script=problem_data.get("lecture_script"),
                question=problem_data["question"],
                topic_category=problem_data.get("topic_category"),
                task_type=problem_data["task_type"]
            )
        
    except ProblemGenerationError as e:
        logger.error(f"Problem generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"問題の生成に失敗しました。もう一度お試しください。"
        )
    except ExternalAPIError as e:
        logger.error(f"External API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"外部サービスとの通信に失敗しました。しばらく待ってから再試行してください。"
        )
    except Exception as e:
        logger.error(f"Unexpected error in problem generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="予期しないエラーが発生しました。"
        )
