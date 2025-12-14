"""
Integration tests for authentication functionality.
Tests Requirements: 1.1, 1.2
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db
from models import Base, User


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables for auth tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_simple_login_creates_new_user():
    """
    Test that simple login creates a new user when user_id doesn't exist.
    Requirements: 1.1
    """
    response = client.post(
        "/api/auth/simple-login",
        json={"user_id": "new_test_user"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "session_token" in data
    assert "user_id" in data
    assert len(data["session_token"]) > 0
    assert len(data["user_id"]) > 0


def test_simple_login_returns_existing_user():
    """
    Test that simple login returns existing user when user_id already exists.
    Requirements: 1.1
    """
    # First login
    response1 = client.post(
        "/api/auth/simple-login",
        json={"user_id": "existing_user"}
    )
    user_id_1 = response1.json()["user_id"]
    
    # Second login with same user_id
    response2 = client.post(
        "/api/auth/simple-login",
        json={"user_id": "existing_user"}
    )
    user_id_2 = response2.json()["user_id"]
    
    # Should return the same user_id
    assert user_id_1 == user_id_2


def test_verify_session_with_valid_token():
    """
    Test that verify endpoint returns valid for a valid session token.
    Requirements: 1.2
    """
    # Login first
    login_response = client.post(
        "/api/auth/simple-login",
        json={"user_id": "verify_test_user"}
    )
    session_token = login_response.json()["session_token"]
    user_id = login_response.json()["user_id"]
    
    # Verify session
    verify_response = client.get(
        f"/api/auth/verify?session_token={session_token}"
    )
    
    assert verify_response.status_code == 200
    data = verify_response.json()
    
    assert data["valid"] is True
    assert data["user_id"] == user_id
    assert data["user_identifier"] == "verify_test_user"


def test_verify_session_with_invalid_token():
    """
    Test that verify endpoint returns 401 for an invalid session token.
    Requirements: 1.2
    """
    verify_response = client.get(
        "/api/auth/verify?session_token=invalid_token_12345"
    )
    
    assert verify_response.status_code == 401
    assert "Invalid or expired session" in verify_response.json()["detail"]


def test_session_token_uniqueness():
    """
    Test that each login generates a unique session token.
    Requirements: 1.1
    """
    response1 = client.post(
        "/api/auth/simple-login",
        json={"user_id": "token_test_user"}
    )
    token1 = response1.json()["session_token"]
    
    response2 = client.post(
        "/api/auth/simple-login",
        json={"user_id": "token_test_user"}
    )
    token2 = response2.json()["session_token"]
    
    # Tokens should be different even for the same user
    assert token1 != token2


def test_user_data_association():
    """
    Test that user sessions are correctly associated with user data.
    Requirements: 1.3
    """
    # Create user via login
    login_response = client.post(
        "/api/auth/simple-login",
        json={"user_id": "association_test_user"}
    )
    session_token = login_response.json()["session_token"]
    user_id = login_response.json()["user_id"]
    
    # Verify the session returns correct user data
    verify_response = client.get(
        f"/api/auth/verify?session_token={session_token}"
    )
    
    verify_data = verify_response.json()
    assert verify_data["user_id"] == user_id
    assert verify_data["user_identifier"] == "association_test_user"
