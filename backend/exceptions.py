"""
Custom exceptions for TOEFL Speaking Master application.
"""
from typing import Optional, Dict, Any


class TOEFLAppException(Exception):
    """基底例外クラス (Base exception class)"""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message
        self.error_code = error_code
        self.details = details or {}


class AuthenticationError(TOEFLAppException):
    """認証エラー (Authentication error)"""
    
    def __init__(self, message: str = "Authentication failed", user_message: Optional[str] = None):
        super().__init__(
            message=message,
            user_message=user_message or "ログインに失敗しました。もう一度お試しください。",
            error_code="AUTH_ERROR"
        )


class ProblemGenerationError(TOEFLAppException):
    """問題生成エラー (Problem generation error)"""
    
    def __init__(self, message: str = "Problem generation failed", user_message: Optional[str] = None):
        super().__init__(
            message=message,
            user_message=user_message or "問題の生成に失敗しました。もう一度お試しください。",
            error_code="PROBLEM_GENERATION_ERROR"
        )


class SpeechProcessingError(TOEFLAppException):
    """音声処理エラー (Speech processing error)"""
    
    def __init__(self, message: str = "Speech processing failed", user_message: Optional[str] = None):
        super().__init__(
            message=message,
            user_message=user_message or "音声の文字起こしに失敗しました。もう一度録音してください。",
            error_code="SPEECH_PROCESSING_ERROR"
        )


class ScoringError(TOEFLAppException):
    """採点エラー (Scoring error)"""
    
    def __init__(self, message: str = "Scoring failed", user_message: Optional[str] = None):
        super().__init__(
            message=message,
            user_message=user_message or "採点処理に失敗しました。もう一度お試しください。",
            error_code="SCORING_ERROR"
        )


class RateLimitExceededError(TOEFLAppException):
    """レート制限超過エラー (Rate limit exceeded error)"""
    
    def __init__(self, message: str = "Rate limit exceeded", user_message: Optional[str] = None):
        super().__init__(
            message=message,
            user_message=user_message or "リクエスト制限を超えました。しばらく待ってから再試行してください。",
            error_code="RATE_LIMIT_EXCEEDED"
        )


class ExternalAPIError(TOEFLAppException):
    """外部API呼び出しエラー (External API call error)"""
    
    def __init__(self, service: str, message: str, user_message: Optional[str] = None):
        self.service = service
        super().__init__(
            message=f"{service} API Error: {message}",
            user_message=user_message or "外部サービスとの通信に失敗しました。しばらく待ってから再試行してください。",
            error_code="EXTERNAL_API_ERROR",
            details={"service": service}
        )


class ValidationError(TOEFLAppException):
    """バリデーションエラー (Validation error)"""
    
    def __init__(self, message: str, user_message: Optional[str] = None, field: Optional[str] = None):
        super().__init__(
            message=message,
            user_message=user_message or "入力データが正しくありません。",
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )
