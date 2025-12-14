"""
Phrases router for managing saved phrases.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import User, SavedPhrase
from repositories.phrase_repository import PhraseRepository

router = APIRouter(prefix="/api/phrases", tags=["phrases"])


def get_user_by_identifier(db: Session, user_id: str) -> User:
    """
    Get user by identifier or raise 404.
    
    Args:
        db: Database session
        user_id: User identifier
    
    Returns:
        User object
    
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.user_identifier == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_phrase_with_authorization(
    repo: PhraseRepository,
    phrase_id: str,
    user: User
) -> tuple[UUID, SavedPhrase]:
    """
    Get phrase by ID and verify user authorization.
    
    Args:
        repo: Phrase repository
        phrase_id: Phrase ID string
        user: User object for authorization
    
    Returns:
        Tuple of (phrase_uuid, phrase_object)
    
    Raises:
        HTTPException: If phrase ID invalid, not found, or unauthorized
    """
    try:
        phrase_uuid = UUID(phrase_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid phrase ID format")
    
    phrase = repo.get_phrase(phrase_uuid)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    if phrase.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this phrase"
        )
    
    return phrase_uuid, phrase


class PhraseSaveRequest(BaseModel):
    """Request model for saving a phrase."""
    user_id: str
    phrase: str
    context: str
    category: str


class PhraseSaveResponse(BaseModel):
    """Response model for phrase save operation."""
    phrase_id: str
    created_at: datetime
    message: str


class SavedPhraseResponse(BaseModel):
    """Response model for a saved phrase."""
    id: str
    phrase: str
    context: str | None
    category: str | None
    is_mastered: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PhrasesListResponse(BaseModel):
    """Response model for list of phrases."""
    phrases: List[SavedPhraseResponse]
    total: int


class PhraseUpdateRequest(BaseModel):
    """Request model for updating phrase mastered status."""
    is_mastered: bool


@router.post("", response_model=PhraseSaveResponse)
async def save_phrase(
    request: PhraseSaveRequest,
    db: Session = Depends(get_db)
):
    """
    Save a new phrase for a user.
    
    Args:
        request: Phrase save request containing user_id, phrase, context, and category
        db: Database session
    
    Returns:
        PhraseSaveResponse with phrase_id and created_at
    """
    user = get_user_by_identifier(db, request.user_id)
    
    repo = PhraseRepository(db)
    saved_phrase = repo.save_phrase(
        user_id=user.id,
        phrase=request.phrase,
        context=request.context,
        category=request.category
    )
    
    return PhraseSaveResponse(
        phrase_id=str(saved_phrase.id),
        created_at=saved_phrase.created_at,
        message="フレーズが保存されました"
    )


@router.get("", response_model=PhrasesListResponse)
async def get_phrases(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all saved phrases for a user.
    
    Args:
        user_id: User identifier
        db: Database session
    
    Returns:
        PhrasesListResponse with list of phrases
    """
    user = get_user_by_identifier(db, user_id)
    
    repo = PhraseRepository(db)
    phrases = repo.get_user_phrases(user.id)
    
    phrase_responses = [
        SavedPhraseResponse(
            id=str(phrase.id),
            phrase=phrase.phrase,
            context=phrase.context,
            category=phrase.category,
            is_mastered=phrase.is_mastered,
            created_at=phrase.created_at
        )
        for phrase in phrases
    ]
    
    return PhrasesListResponse(
        phrases=phrase_responses,
        total=len(phrase_responses)
    )


@router.delete("/{phrase_id}")
async def delete_phrase(
    phrase_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a saved phrase.
    
    Args:
        phrase_id: UUID of the phrase to delete
        user_id: User identifier (for authorization)
        db: Database session
    
    Returns:
        Success message
    """
    user = get_user_by_identifier(db, user_id)
    repo = PhraseRepository(db)
    phrase_uuid, _ = get_phrase_with_authorization(repo, phrase_id, user)
    
    repo.delete_phrase(phrase_uuid)
    
    return {"message": "フレーズが削除されました"}


@router.patch("/{phrase_id}", response_model=SavedPhraseResponse)
async def update_phrase(
    phrase_id: str,
    request: PhraseUpdateRequest,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Update a phrase's mastered status.
    
    Args:
        phrase_id: UUID of the phrase to update
        request: Update request with is_mastered status
        user_id: User identifier (for authorization)
        db: Database session
    
    Returns:
        Updated SavedPhraseResponse
    """
    user = get_user_by_identifier(db, user_id)
    repo = PhraseRepository(db)
    phrase_uuid, _ = get_phrase_with_authorization(repo, phrase_id, user)
    
    updated_phrase = repo.update_mastered_status(phrase_uuid, request.is_mastered)
    
    return SavedPhraseResponse(
        id=str(updated_phrase.id),
        phrase=updated_phrase.phrase,
        context=updated_phrase.context,
        category=updated_phrase.category,
        is_mastered=updated_phrase.is_mastered,
        created_at=updated_phrase.created_at
    )
