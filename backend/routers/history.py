"""
History router for retrieving practice session history.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import PracticeSession, User

router = APIRouter(prefix="/api/history", tags=["history"])


class PracticeSessionSummary(BaseModel):
    """Summary of a practice session for history display."""
    session_id: str
    created_at: datetime
    task_type: str
    overall_score: int | None

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    """Response containing practice session history."""
    sessions: List[PracticeSessionSummary]
    total: int


class ScoringDetail(BaseModel):
    """Scoring detail for a specific dimension."""
    score: int
    feedback: str


class SessionDetailResponse(BaseModel):
    """Detailed information about a practice session."""
    session_id: str
    created_at: datetime
    task_type: str
    reading_text: str
    lecture_script: str
    question: str
    user_transcript: str | None
    overall_score: int | None
    delivery_score: int | None
    language_use_score: int | None
    topic_dev_score: int | None
    feedback: dict | None
    model_answer: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=HistoryResponse)
async def get_history(
    user_id: str,
    limit: int = 3,
    db: Session = Depends(get_db)
):
    """
    Get recent practice session history for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of sessions to return (default: 3)
        db: Database session
    
    Returns:
        HistoryResponse with list of recent sessions
    """
    # Verify user exists
    user = db.query(User).filter(User.user_identifier == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Query recent sessions
    sessions = (
        db.query(PracticeSession)
        .filter(PracticeSession.user_id == user.id)
        .order_by(PracticeSession.created_at.desc())
        .limit(limit)
        .all()
    )
    
    # Convert to response format
    session_summaries = [
        PracticeSessionSummary(
            session_id=str(session.id),
            created_at=session.created_at,
            task_type=session.task_type,
            overall_score=session.overall_score
        )
        for session in sessions
    ]
    
    return HistoryResponse(
        sessions=session_summaries,
        total=len(session_summaries)
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific practice session.
    
    Args:
        session_id: Session identifier
        user_id: User identifier for authorization
        db: Database session
    
    Returns:
        SessionDetailResponse with complete session information
    """
    # Verify user exists
    user = db.query(User).filter(User.user_identifier == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Query session
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    session = (
        db.query(PracticeSession)
        .filter(
            PracticeSession.id == session_uuid,
            PracticeSession.user_id == user.id
        )
        .first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionDetailResponse(
        session_id=str(session.id),
        created_at=session.created_at,
        task_type=session.task_type,
        reading_text=session.reading_text,
        lecture_script=session.lecture_script,
        question=session.question,
        user_transcript=session.user_transcript,
        overall_score=session.overall_score,
        delivery_score=session.delivery_score,
        language_use_score=session.language_use_score,
        topic_dev_score=session.topic_dev_score,
        feedback=session.feedback_json,
        model_answer=session.model_answer
    )
