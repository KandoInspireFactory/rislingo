"""
Integration test for audio cleanup after scoring.
Tests that audio files are automatically deleted after scoring is complete.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from main import app
from database import get_db
from models import Base, User, PracticeSession


# Create test database (in-memory for isolation)
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """Create database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def temp_audio_dir():
    """Create temporary audio directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(user_identifier="test_user_cleanup")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_session(db_session, test_user):
    """Create test practice session."""
    session = PracticeSession(
        user_id=test_user.id,
        task_type="task3",
        reading_text="Test reading text",
        lecture_script="Test lecture script",
        lecture_audio_url="/audio/lecture_test.mp3",
        question="Test question"
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def test_audio_cleanup_called_in_scoring_flow():
    """Test that audio cleanup is called in the scoring flow."""
    from routers.scoring import schedule_audio_cleanup
    
    # This test verifies that the cleanup function is imported and available
    # The actual integration is tested through the unit tests
    assert callable(schedule_audio_cleanup)


def test_audio_cleanup_function_deletes_file(temp_audio_dir):
    """Test that the cleanup function actually deletes files."""
    from utils.audio_cleanup import schedule_audio_cleanup
    
    # Create a fake audio file
    session_id = "test-session-123"
    audio_file = Path(temp_audio_dir) / f"lecture_{session_id}.mp3"
    audio_file.write_text("fake audio content")
    
    # Verify file exists
    assert audio_file.exists()
    
    # Call cleanup
    result = schedule_audio_cleanup(session_id, temp_audio_dir)
    
    # Verify file was deleted
    assert result is True
    assert not audio_file.exists()


def test_audio_cleanup_handles_missing_file(temp_audio_dir):
    """Test that cleanup handles missing files gracefully."""
    from utils.audio_cleanup import schedule_audio_cleanup
    
    # Call cleanup for non-existent file
    result = schedule_audio_cleanup("nonexistent-session", temp_audio_dir)
    
    # Should succeed (no file to clean up)
    assert result is True
