"""
Tests for HTTPS redirect middleware.
"""
import pytest
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from middleware.https_redirect import HTTPSRedirectMiddleware


@pytest.fixture
def app_with_https():
    """Create a test app with HTTPS redirect."""
    app = FastAPI()
    app.add_middleware(HTTPSRedirectMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    return app


@pytest.fixture
def client(app_with_https):
    """Create test client."""
    return TestClient(app_with_https)


def test_localhost_allows_http(client):
    """Test that localhost allows HTTP in development."""
    # TestClient uses localhost by default
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}


def test_development_environment_allows_http(app_with_https, monkeypatch):
    """Test that development environment allows HTTP."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    
    client = TestClient(app_with_https)
    response = client.get("/test")
    assert response.status_code == 200


def test_https_request_passes_through(client):
    """Test that HTTPS requests pass through normally."""
    # Simulate HTTPS by setting X-Forwarded-Proto header
    headers = {"X-Forwarded-Proto": "https"}
    response = client.get("/test", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "success"}


def test_middleware_checks_forwarded_proto_header(client):
    """Test that middleware checks X-Forwarded-Proto header."""
    # This header is set by proxies/load balancers
    headers = {"X-Forwarded-Proto": "https"}
    response = client.get("/test", headers=headers)
    assert response.status_code == 200
