"""
Tests for history router endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

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


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_get_history_empty():
    """Test getting history for user with no sessions."""
    # Create user
    db = TestingSessionLocal()
    user = User(user_identifier="test_user_empty")
    db.add(user)
    db.commit()
    db.close()
    
    # Get history
    response = client.get("/api/history?user_id=test_user_empty")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["sessions"]) == 0


def test_get_history_with_sessions():
    """Test getting history for user with sessions."""
    # Create user
    db = TestingSessionLocal()
    user = User(user_identifier="test_user_sessions")
    db.add(user)
    db.commit()
    
    # Create practice sessions
    session1 = PracticeSession(
        user_id=user.id,
        task_type="task3",
        reading_text="Reading 1",
        lecture_script="Lecture 1",
        question="Question 1",
        overall_score=3
    )
    session2 = PracticeSession(
        user_id=user.id,
        task_type="task3",
        reading_text="Reading 2",
        lecture_script="Lecture 2",
        question="Question 2",
        overall_score=4
    )
    db.add(session1)
    db.add(session2)
    db.commit()
    db.close()
    
    # Get history
    response = client.get("/api/history?user_id=test_user_sessions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["sessions"]) == 2
    assert data["sessions"][0]["task_type"] == "task3"
    assert data["sessions"][0]["overall_score"] == 4  # Most recent first


def test_get_history_limit():
    """Test history limit parameter."""
    # Create user
    db = TestingSessionLocal()
    user = User(user_identifier="test_user_limit")
    db.add(user)
    db.commit()
    
    # Create 5 practice sessions
    for i in range(5):
        session = PracticeSession(
            user_id=user.id,
            task_type="task3",
            reading_text=f"Reading {i}",
            lecture_script=f"Lecture {i}",
            question=f"Question {i}",
            overall_score=i % 5
        )
        db.add(session)
    db.commit()
    db.close()
    
    # Get history with limit=3
    response = client.get("/api/history?user_id=test_user_limit&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["sessions"]) == 3


def test_get_history_user_not_found():
    """Test getting history for non-existent user."""
    response = client.get("/api/history?user_id=nonexistent_user")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_session_detail():
    """Test getting detailed information about a specific session."""
    # Create user
    db = TestingSessionLocal()
    user = User(user_identifier="test_user_detail")
    db.add(user)
    db.commit()
    
    # Create practice session with full details
    session = PracticeSession(
        user_id=user.id,
        task_type="task3",
        reading_text="Test reading text",
        lecture_script="Test lecture script",
        question="Test question",
        user_transcript="Test transcript",
        overall_score=3,
        delivery_score=3,
        language_use_score=3,
        topic_dev_score=3,
        feedback_json={
            "delivery": {"score": 3, "feedback": "Good delivery"},
            "language_use": {"score": 3, "feedback": "Good language"},
            "topic_development": {"score": 3, "feedback": "Good development"},
            "improvement_tips": ["Tip 1", "Tip 2"]
        },
        model_answer="Test model answer"
    )
    db.add(session)
    db.commit()
    session_id = str(session.id)
    db.close()
    
    # Get session detail
    response = client.get(f"/api/history/{session_id}?user_id=test_user_detail")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["task_type"] == "task3"
    assert data["reading_text"] == "Test reading text"
    assert data["lecture_script"] == "Test lecture script"
    assert data["question"] == "Test question"
    assert data["user_transcript"] == "Test transcript"
    assert data["overall_score"] == 3
    assert data["delivery_score"] == 3
    assert data["language_use_score"] == 3
    assert data["topic_dev_score"] == 3
    assert data["feedback"] is not None
    assert data["model_answer"] == "Test model answer"


def test_get_session_detail_not_found():
    """Test getting detail for non-existent session."""
    # Create user
    db = TestingSessionLocal()
    user = User(user_identifier="test_user_not_found")
    db.add(user)
    db.commit()
    db.close()
    
    # Try to get non-existent session
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/history/{fake_uuid}?user_id=test_user_not_found")
    assert response.status_code == 404


def test_get_session_detail_wrong_user():
    """Test getting detail for session belonging to different user."""
    # Create two users
    db = TestingSessionLocal()
    user1 = User(user_identifier="test_user_1")
    user2 = User(user_identifier="test_user_2")
    db.add(user1)
    db.add(user2)
    db.commit()
    
    # Create session for user1
    session = PracticeSession(
        user_id=user1.id,
        task_type="task3",
        reading_text="Reading",
        lecture_script="Lecture",
        question="Question"
    )
    db.add(session)
    db.commit()
    session_id = str(session.id)
    db.close()
    
    # Try to access with user2
    response = client.get(f"/api/history/{session_id}?user_id=test_user_2")
    assert response.status_code == 404


def test_get_session_detail_invalid_uuid():
    """Test getting detail with invalid session ID format."""
    # Create user
    db = TestingSessionLocal()
    user = User(user_identifier="test_user_invalid")
    db.add(user)
    db.commit()
    db.close()
    
    # Try with invalid UUID
    response = client.get("/api/history/invalid-uuid?user_id=test_user_invalid")
    assert response.status_code == 400
