"""
SQLAlchemy database models for TOEFL Speaking Master application.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import TypeDecorator

# Create a type that uses JSONB for PostgreSQL and JSON for other databases
class JSONType(TypeDecorator):
    """Platform-independent JSON type."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

Base = declarative_base()


class User(Base):
    """User model for simple authentication."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_identifier = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    practice_sessions = relationship("PracticeSession", back_populates="user", cascade="all, delete-orphan")
    saved_phrases = relationship("SavedPhrase", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, user_identifier={self.user_identifier})>"


class PracticeSession(Base):
    """Practice session model storing problem, transcript, and scoring results."""
    __tablename__ = "practice_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    task_type = Column(String(20), nullable=False, default="task3")
    reading_text = Column(Text, nullable=True)  # Task1では不要
    lecture_script = Column(Text, nullable=True)  # Task1では不要
    lecture_audio_url = Column(String(500))
    question = Column(Text, nullable=False)
    user_transcript = Column(Text)
    overall_score = Column(Integer, CheckConstraint("overall_score >= 0 AND overall_score <= 4"))
    delivery_score = Column(Integer, CheckConstraint("delivery_score >= 0 AND delivery_score <= 4"))
    language_use_score = Column(Integer, CheckConstraint("language_use_score >= 0 AND language_use_score <= 4"))
    topic_dev_score = Column(Integer, CheckConstraint("topic_dev_score >= 0 AND topic_dev_score <= 4"))
    feedback_json = Column(JSONType)
    model_answer = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="practice_sessions")

    def __repr__(self):
        return f"<PracticeSession(id={self.id}, user_id={self.user_id}, task_type={self.task_type})>"


class SavedPhrase(Base):
    """Saved phrase model for flashcard functionality."""
    __tablename__ = "saved_phrases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    phrase = Column(Text, nullable=False)
    context = Column(Text)
    category = Column(String(50))
    is_mastered = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="saved_phrases")

    def __repr__(self):
        return f"<SavedPhrase(id={self.id}, phrase={self.phrase[:30]}...)>"
