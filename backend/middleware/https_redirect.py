"""
HTTPS redirect middleware for TOEFL Speaking Master API.
Enforces HTTPS communication for all requests.
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
import os


logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS communication.
    
    In production, redirects all HTTP requests to HTTPS.
    In development (localhost), allows HTTP for testing.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and enforce HTTPS if needed.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response (redirect to HTTPS or normal response)
        """
        # Get environment setting
        environment = os.getenv("ENVIRONMENT", "development")
        
        # Skip HTTPS enforcement in development or for localhost
        if environment == "development" or request.url.hostname in ["localhost", "127.0.0.1"]:
            return await call_next(request)
        
        # Check if request is using HTTPS
        # Check both the scheme and X-Forwarded-Proto header (for proxies)
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
        
        if request.url.scheme != "https" and forwarded_proto != "https":
            # Redirect to HTTPS
            https_url = request.url.replace(scheme="https")
            logger.warning(f"Redirecting HTTP request to HTTPS: {request.url} -> {https_url}")
            return RedirectResponse(url=str(https_url), status_code=301)
        
        # Request is already HTTPS, proceed normally
        return await call_next(request)
