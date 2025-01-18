from typing import Dict, Any
from pydantic import BaseModel, Field

class AuthHeaders(BaseModel):
    headers: Dict[str, str] = Field(..., description="Authentication headers")

class AuthCredentials(BaseModel):
    auth_type: str = Field(..., description="Authentication type")
    credentials: Dict[str, Any] = Field(..., description="Authentication credentials") 