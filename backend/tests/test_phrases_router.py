"""
Tests for phrases router endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from main import app
from database import get_db
from models import User, SavedPhrase


# Test database setup - only create tables we need (in-memory for isolation)
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
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
    # Only create the tables we need for phrase testing
    User.__table__.create(bind=engine, checkfirst=True)
    SavedPhrase.__table__.create(bind=engine, checkfirst=True)
    yield
    SavedPhrase.__table__.drop(bind=engine, checkfirst=True)
    User.__table__.drop(bind=engine, checkfirst=True)


@pytest.fixture
def test_user():
    """Create a test user."""
    db = TestingSessionLocal()
    user = User(user_identifier="test_user_phrases")
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    user_identifier = user.user_identifier
    db.close()
    return {"id": user_id, "identifier": user_identifier}


def test_save_phrase(test_user):
    """Test saving a new phrase."""
    response = client.post(
        "/api/phrases",
        json={
            "user_id": test_user["identifier"],
            "phrase": "In my opinion",
            "context": "Used to introduce personal viewpoint",
            "category": "transition"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "phrase_id" in data
    assert "created_at" in data
    assert data["message"] == "フレーズが保存されました"


def test_save_phrase_user_not_found():
    """Test saving phrase with non-existent user."""
    response = client.post(
        "/api/phrases",
        json={
            "user_id": "nonexistent_user",
            "phrase": "Test phrase",
            "context": "Test context",
            "category": "transition"
        }
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_phrases(test_user):
    """Test retrieving all phrases for a user."""
    # First, save some phrases
    phrases_to_save = [
        {"phrase": "First of all", "context": "Introduction", "category": "transition"},
        {"phrase": "For example", "context": "Example", "category": "example"},
        {"phrase": "In conclusion", "context": "Conclusion", "category": "conclusion"}
    ]
    
    for phrase_data in phrases_to_save:
        client.post(
            "/api/phrases",
            json={
                "user_id": test_user["identifier"],
                **phrase_data
            }
        )
    
    # Get phrases
    response = client.get(f"/api/phrases?user_id={test_user['identifier']}")
    
    assert response.status_code == 200
    data = response.json()
    assert "phrases" in data
    assert "total" in data
    assert data["total"] == 3
    assert len(data["phrases"]) == 3


def test_delete_phrase(test_user):
    """Test deleting a phrase."""
    # First, save a phrase
    save_response = client.post(
        "/api/phrases",
        json={
            "user_id": test_user["identifier"],
            "phrase": "To be deleted",
            "context": "Test context",
            "category": "transition"
        }
    )
    phrase_id = save_response.json()["phrase_id"]
    
    # Delete the phrase
    response = client.delete(
        f"/api/phrases/{phrase_id}?user_id={test_user['identifier']}"
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "フレーズが削除されました"
    
    # Verify it's deleted
    get_response = client.get(f"/api/phrases?user_id={test_user['identifier']}")
    assert get_response.json()["total"] == 0


def test_delete_phrase_not_found():
    """Test deleting non-existent phrase."""
    fake_id = str(uuid4())
    response = client.delete(
        f"/api/phrases/{fake_id}?user_id=test_user"
    )
    
    assert response.status_code == 404


def test_update_phrase_mastered(test_user):
    """Test updating phrase mastered status."""
    # First, save a phrase
    save_response = client.post(
        "/api/phrases",
        json={
            "user_id": test_user["identifier"],
            "phrase": "To be mastered",
            "context": "Test context",
            "category": "transition"
        }
    )
    phrase_id = save_response.json()["phrase_id"]
    
    # Update mastered status
    response = client.patch(
        f"/api/phrases/{phrase_id}?user_id={test_user['identifier']}",
        json={"is_mastered": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_mastered"] is True
    assert data["phrase"] == "To be mastered"


def test_update_phrase_unauthorized(test_user):
    """Test updating phrase belonging to another user."""
    # Create another user
    db = TestingSessionLocal()
    other_user = User(user_identifier="other_user")
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    
    # Save phrase for test_user
    save_response = client.post(
        "/api/phrases",
        json={
            "user_id": test_user["identifier"],
            "phrase": "Test phrase",
            "context": "Test context",
            "category": "transition"
        }
    )
    phrase_id = save_response.json()["phrase_id"]
    db.close()
    
    # Try to update with other_user
    response = client.patch(
        f"/api/phrases/{phrase_id}?user_id=other_user",
        json={"is_mastered": True}
    )
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this phrase"
