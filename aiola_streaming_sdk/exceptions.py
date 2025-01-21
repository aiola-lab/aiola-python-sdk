from pydantic import BaseModel
from typing import Optional

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None

class AiolaStreamingError(Exception):
    """Base exception for all SDK errors"""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.error = ErrorDetail(
            code="STREAMING_ERROR",
            message=message,
            details=details
        )
        super().__init__(message)

class ConnectionError(AiolaStreamingError):
    """Raised when connection to the streaming server fails"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message,
            ErrorDetail(
                code="CONNECTION_ERROR",
                message=message,
                details=details
            )
        )

class AuthenticationError(AiolaStreamingError):
    """Raised when authentication fails"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message,
            ErrorDetail(
                code="AUTH_ERROR",
                message=message,
                details=details
            )
        ) 