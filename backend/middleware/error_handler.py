"""
Global error handler middleware for unified error responses.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Union

from exceptions import (
    TOEFLAppException,
    AuthenticationError,
    ProblemGenerationError,
    SpeechProcessingError,
    ScoringError,
    RateLimitExceededError,
    ExternalAPIError,
    ValidationError
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class ErrorResponse:
    """Unified error response format."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        user_message: str,
        details: dict = None,
        status_code: int = 500
    ):
        self.error_code = error_code
        self.message = message
        self.user_message = user_message
        self.details = details or {}
        self.status_code = status_code
    
    def to_dict(self):
        """Convert to dictionary for JSON response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "user_message": self.user_message,
                "details": self.details
            },
            # Backward compatibility: include detail field for tests
            "detail": self.message
        }


async def toefl_exception_handler(request: Request, exc: TOEFLAppException) -> JSONResponse:
    """
    Handle custom TOEFL application exceptions.
    """
    # Map exception types to HTTP status codes
    status_code_map = {
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
        ExternalAPIError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ValidationError: status.HTTP_400_BAD_REQUEST,
        ProblemGenerationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        SpeechProcessingError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ScoringError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log the error
    logger.error(
        f"Application error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path
        }
    )
    
    error_response = ErrorResponse(
        error_code=exc.error_code or "INTERNAL_ERROR",
        message=exc.message,
        user_message=exc.user_message,
        details=exc.details,
        status_code=status_code
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.to_dict()
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle standard HTTP exceptions.
    """
    # Map status codes to user-friendly messages
    user_messages = {
        400: "リクエストが正しくありません。",
        401: "認証が必要です。",
        403: "アクセスが拒否されました。",
        404: "リソースが見つかりません。",
        429: "リクエスト制限を超えました。しばらく待ってから再試行してください。",
        500: "サーバーエラーが発生しました。",
        503: "サービスが一時的に利用できません。"
    }
    
    user_message = user_messages.get(exc.status_code, "エラーが発生しました。")
    
    # Log the error
    logger.warning(
        f"HTTP error: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )
    
    error_response = ErrorResponse(
        error_code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        user_message=user_message,
        status_code=exc.status_code
    )
    # Log the exact payload we will return for easier debugging
    logger.debug("Returning HTTP exception payload", extra={"payload": error_response.to_dict()})
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation errors (Pydantic validation).
    """
    # Extract validation error details
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation error: {errors}",
        extra={
            "path": request.url.path,
            "errors": errors
        }
    )
    
    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        user_message="入力データが正しくありません。入力内容を確認してください。",
        details={"validation_errors": errors},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    logger.debug("Returning validation exception payload", extra={"payload": error_response.to_dict()})
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.to_dict()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.
    """
    # Log the full exception for debugging
    logger.exception(
        f"Unexpected error: {str(exc)}",
        extra={
            "path": request.url.path,
            "exception_type": type(exc).__name__
        }
    )
    
    error_response = ErrorResponse(
        error_code="INTERNAL_ERROR",
        message=f"Internal server error: {type(exc).__name__}",
        user_message="予期しないエラーが発生しました。しばらく待ってから再試行してください。",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    logger.debug("Returning generic exception payload", extra={"payload": error_response.to_dict()})
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.to_dict()
    )
