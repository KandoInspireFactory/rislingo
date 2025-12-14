"""
Rate limiting middleware for TOEFL Speaking Master API.
Implements per-user rate limiting to prevent abuse.
"""
import logging
import time
from collections import defaultdict
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status


logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting per user.
    
    Limits: 100 requests per minute per user
    Uses a sliding window approach with request timestamps.
    """
    
    def __init__(self, app, requests_per_minute: int = 100):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests allowed per minute per user
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 60 seconds = 1 minute
        
        # Store request timestamps per user: {user_id: [timestamp1, timestamp2, ...]}
        self.request_history: Dict[str, list] = defaultdict(list)
        
        logger.info(f"RateLimitMiddleware initialized: {requests_per_minute} requests/minute")
    
    def _get_user_identifier(self, request: Request) -> str:
        """
        Extract user identifier from request.
        
        Priority:
        1. User ID from session/auth header
        2. IP address as fallback
        
        Args:
            request: Incoming request
            
        Returns:
            User identifier string
        """
        # Try to get user_id from Authorization header or session
        auth_header = request.headers.get("Authorization", "")
        if auth_header and auth_header.startswith("Bearer "):
            # Use the token as identifier (in production, decode JWT to get user_id)
            return auth_header[7:]  # Remove "Bearer " prefix
        
        # Fallback to IP address
        # Check X-Forwarded-For header first (for proxies)
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            # Use direct client IP
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _clean_old_requests(self, user_id: str, current_time: float):
        """
        Remove request timestamps older than the window size.
        
        Args:
            user_id: User identifier
            current_time: Current timestamp
        """
        cutoff_time = current_time - self.window_size
        self.request_history[user_id] = [
            ts for ts in self.request_history[user_id]
            if ts > cutoff_time
        ]
    
    def _is_rate_limited(self, user_id: str, current_time: float) -> Tuple[bool, int]:
        """
        Check if user has exceeded rate limit.
        
        Args:
            user_id: User identifier
            current_time: Current timestamp
            
        Returns:
            Tuple of (is_limited, remaining_requests)
        """
        # Clean old requests
        self._clean_old_requests(user_id, current_time)
        
        # Count requests in current window
        request_count = len(self.request_history[user_id])
        
        # Check if limit exceeded
        is_limited = request_count >= self.requests_per_minute
        remaining = max(0, self.requests_per_minute - request_count)
        
        return is_limited, remaining
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and enforce rate limiting.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response (rate limit error or normal response)
        """
        # Skip rate limiting for health check endpoints
        if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get user identifier
        user_id = self._get_user_identifier(request)
        current_time = time.time()
        
        # Check rate limit
        is_limited, remaining = self._is_rate_limited(user_id, current_time)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for user: {user_id}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "リクエスト制限を超えました。しばらく待ってから再試行してください。",
                    "error": "rate_limit_exceeded",
                    "retry_after": self.window_size
                },
                headers={
                    "Retry-After": str(self.window_size),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + self.window_size))
                }
            )
        
        # Record this request
        self.request_history[user_id].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)  # -1 for current request
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))
        
        return response
