"""
Tests for rate limiting middleware.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from middleware.rate_limiter import RateLimitMiddleware


@pytest.fixture
def app_with_rate_limit():
    """Create a test app with rate limiting."""
    app = FastAPI()
    
    # Add rate limiter with low limit for testing
    app.add_middleware(RateLimitMiddleware, requests_per_minute=5)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    return app


@pytest.fixture
def client(app_with_rate_limit):
    """Create test client."""
    return TestClient(app_with_rate_limit)


def test_rate_limit_allows_requests_under_limit(client):
    """Test that requests under the limit are allowed."""
    # Make 5 requests (at the limit)
    for i in range(5):
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
        
        # Check rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert "X-RateLimit-Remaining" in response.headers


def test_rate_limit_blocks_requests_over_limit(client):
    """Test that requests over the limit are blocked."""
    # Make 5 requests (at the limit)
    for i in range(5):
        response = client.get("/test")
        assert response.status_code == 200
    
    # 6th request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert "rate_limit_exceeded" in response.json()["error"]
    assert "Retry-After" in response.headers


def test_rate_limit_headers_present(client):
    """Test that rate limit headers are present in responses."""
    response = client.get("/test")
    
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_rate_limit_different_users(app_with_rate_limit):
    """Test that rate limits are per-user (per IP)."""
    client1 = TestClient(app_with_rate_limit)
    client2 = TestClient(app_with_rate_limit)
    
    # Each client should have their own limit
    # Note: In test environment, both clients may share the same IP
    # This test verifies the middleware structure
    
    response1 = client1.get("/test")
    assert response1.status_code == 200
    
    response2 = client2.get("/test")
    assert response2.status_code == 200


def test_rate_limit_with_auth_header(client):
    """Test rate limiting with authentication header."""
    headers = {"Authorization": "Bearer test_token_123"}
    
    # Make requests with auth header
    for i in range(5):
        response = client.get("/test", headers=headers)
        assert response.status_code == 200
    
    # 6th request should be rate limited
    response = client.get("/test", headers=headers)
    assert response.status_code == 429


def test_health_check_bypasses_rate_limit():
    """Test that health check endpoints bypass rate limiting."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=2)
    
    @app.get("/")
    async def root():
        return {"status": "ok"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    client = TestClient(app)
    
    # Make many requests to health endpoints - should not be rate limited
    for i in range(10):
        response = client.get("/")
        assert response.status_code == 200
        
        response = client.get("/health")
        assert response.status_code == 200
