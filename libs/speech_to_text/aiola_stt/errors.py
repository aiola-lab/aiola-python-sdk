"""
Error classes for the aiOla SDK.
"""

from typing import Dict, Optional
from enum import Enum

class AiolaErrorCode(str, Enum):
    """Error codes for aiOla streaming service errors."""
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    NETWORK_ERROR = "NETWORK_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    KEYWORDS_ERROR = "KEYWORDS_ERROR"
    MIC_ERROR = "MIC_ERROR"
    MIC_ALREADY_IN_USE = "MIC_ALREADY_IN_USE"
    STREAMING_ERROR = "STREAMING_ERROR"
    GENERAL_ERROR = "GENERAL_ERROR"
    
class AiolaError(Exception):
    """Custom error class for aiOla SDK"""
    def __init__(
        self,
        message: str,
        code: AiolaErrorCode = AiolaErrorCode.GENERAL_ERROR,
        details: Optional[Dict] = None
    ):
        super().__init__(message)
        self.name = "AiolaError"
        self.code = code
        self.details = details or {}
        self.message = message

    def __str__(self) -> str:
        return f"{self.name} [{self.code}]: {self.message}"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "message": str(self.message),
            "code": self.code,
            "details": self.details,
            "stack": self.__traceback__
        } 
        
