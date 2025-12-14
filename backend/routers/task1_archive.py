"""
Task1 Archive router for TOEFL Speaking Master API.
Handles retrieval of past Task1 questions and responses.
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import PracticeSession, User
from exceptions import ValidationError


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/task1-archive",
    tags=["task1-archive"]
)


# Response models
class Task1QuestionResponse(BaseModel):
    """Response model for a Task1 question."""
    id: str = Field(..., description="Session ID")
    question: str = Field(..., description="The Task1 question")
    user_transcript: Optional[str] = Field(None, description="User's response transcript")
    overall_score: Optional[int] = Field(None, description="Overall score (0-4)")
    created_at: str = Field(..., description="When the question was attempted")


class Task1ArchiveResponse(BaseModel):
    """Response model for Task1 archive."""
    questions: List[Task1QuestionResponse] = Field(..., description="List of Task1 questions")
    total: int = Field(..., description="Total number of questions")


@router.get("/questions", response_model=Task1ArchiveResponse)
async def get_task1_questions(
    user_id: str = Query(..., description="User identifier"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of questions to return"),
    offset: int = Query(0, ge=0, description="Number of questions to skip"),
    db: Session = Depends(get_db)
):
    """
    Get Task1 questions for a user.
    
    Returns a list of Task1 questions that the user has attempted,
    ordered by creation date (most recent first).
    
    Args:
        user_id: User identifier
        limit: Maximum number of questions to return (1-100)
        offset: Number of questions to skip for pagination
        db: Database session
        
    Returns:
        Task1ArchiveResponse with questions and total count
        
    Raises:
        HTTPException: If user not found or database error
    """
    try:
        logger.info(f"Fetching Task1 questions for user: {user_id}")
        
        # Find user by identifier
        user = db.query(User).filter(User.user_identifier == user_id).first()
        if not user:
                raise HTTPException(status_code=404, detail="User not found")
        
        # Query Task1 sessions for this user
        query = db.query(PracticeSession).filter(
            PracticeSession.user_id == user.id,
            PracticeSession.task_type == "task1"
        ).order_by(desc(PracticeSession.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        sessions = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        questions = []
        for session in sessions:
            questions.append(Task1QuestionResponse(
                id=str(session.id),
                question=session.question,
                user_transcript=session.user_transcript,
                overall_score=session.overall_score,
                created_at=session.created_at.isoformat()
            ))
        
        logger.info(f"Retrieved {len(questions)} Task1 questions for user {user_id}")
        
        return Task1ArchiveResponse(
            questions=questions,
            total=total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Task1 questions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Task1 questions")


@router.get("/questions/{question_id}", response_model=Task1QuestionResponse)
async def get_task1_question(
    question_id: str,
    user_id: str = Query(..., description="User identifier"),
    db: Session = Depends(get_db)
):
    """
    Get a specific Task1 question by ID.
    
    Args:
        question_id: Session ID of the Task1 question
        user_id: User identifier
        db: Database session
        
    Returns:
        Task1QuestionResponse with question details
        
    Raises:
        HTTPException: If question not found or access denied
    """
    try:
        logger.info(f"Fetching Task1 question {question_id} for user {user_id}")
        
        # Validate question_id format
        try:
            question_uuid = UUID(question_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question ID format")
        
        # Find user by identifier
        user = db.query(User).filter(User.user_identifier == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Find the specific Task1 session
        session = db.query(PracticeSession).filter(
            PracticeSession.id == question_uuid,
            PracticeSession.user_id == user.id,
            PracticeSession.task_type == "task1"
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Task1 question not found")
        
        return Task1QuestionResponse(
            id=str(session.id),
            question=session.question,
            user_transcript=session.user_transcript,
            overall_score=session.overall_score,
            created_at=session.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Task1 question {question_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Task1 question")