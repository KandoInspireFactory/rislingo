"""
Authentication router for simple login functionality.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets
from typing import Optional
from uuid import UUID

from database import get_db
from models import User, Session as DBSession # Renamed to avoid conflict with sqlalchemy.orm.Session

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class SimpleLoginRequest(BaseModel):
    """Request model for simple login."""
    user_id: str


class SimpleLoginResponse(BaseModel):
    """Response model for simple login."""
    session_token: str
    user_id: str


def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


def create_or_get_user(db: Session, user_identifier: str) -> User:
    """Create a new user or get existing user by identifier."""
    user = db.query(User).filter(User.user_identifier == user_identifier).first()
    
    if not user:
        user = User(user_identifier=user_identifier)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


@router.post("/simple-login", response_model=SimpleLoginResponse)
async def simple_login(
    request: SimpleLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Simple login endpoint that creates or retrieves a user and generates a session token.
    
    Requirements: 1.1, 1.2
    """
    try:
        # Create or get user
        user = create_or_get_user(db, request.user_id)
        
        # Generate session token
        session_token = generate_session_token()
        expires_at = datetime.utcnow() + timedelta(days=30) # Session expires in 30 days
        
        # Store session in database
        db_session = DBSession(
            user_id=user.id,
            session_token=session_token,
            expires_at=expires_at
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        return SimpleLoginResponse(
            session_token=session_token,
            user_id=str(user.id)
        )
    
    except Exception as e:
        db.rollback() # Rollback in case of error
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


def get_current_user(
    session_token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current user from session token.
    Fetches session from database and checks for expiration.
    Deletes expired sessions.
    """
    if not session_token:
        return None
    
    db_session = db.query(DBSession).filter(DBSession.session_token == session_token).first()
    
    if not db_session:
        return None
    
    # Check if session expired
    if db_session.expires_at < datetime.utcnow():
        db.delete(db_session)
        db.commit()
        return None
    
    # Get user from database
    user = db.query(User).filter(User.id == db_session.user_id).first()
    
    return user


@router.get("/verify")
async def verify_session(
    session_token: str,
    db: Session = Depends(get_db)
):
    """
    Verify if a session token is valid.
    """
    user = get_current_user(session_token, db)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {
        "valid": True,
        "user_id": str(user.id),
        "user_identifier": user.user_identifier
    }

@router.post("/logout")
async def logout(
    session_token: str,
    db: Session = Depends(get_db)
):
    """
    Logs out a user by deleting their session token from the database.
    """
    db_session = db.query(DBSession).filter(DBSession.session_token == session_token).first()
    
    if db_session:
        db.delete(db_session)
        db.commit()
    
    return {"message": "Logged out successfully"}