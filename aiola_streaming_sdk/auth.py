from typing import Dict, Any
from pydantic import BaseModel, Field
from .exceptions import AuthenticationError

class AuthHeaders(BaseModel):
    headers: Dict[str, str] = Field(..., description="Authentication headers")

class AuthCredentials(BaseModel):
    auth_type: str = Field(..., description="Authentication type")
    credentials: Dict[str, Any] = Field(..., description="Authentication credentials")

def get_auth_headers(auth_type: str, auth_credentials: Dict[str, Any]) -> AuthHeaders:
    """Generate authentication headers based on the auth type"""
    
    credentials = AuthCredentials(auth_type=auth_type, credentials=auth_credentials)
    
    if credentials.auth_type == "Cookie":
        if "cookie" not in credentials.credentials:
            raise AuthenticationError("Cookie value is required for Cookie authentication")
        return AuthHeaders(headers={"Cookie": credentials.credentials["cookie"]})
    
    elif credentials.auth_type == "Bearer":
        if "token" not in credentials.credentials:
            raise AuthenticationError("Token is required for Bearer authentication")
        return AuthHeaders(headers={"AUTHORIZATION": f"Bearer {credentials.credentials['token']}"})
    
    elif credentials.auth_type == "x-api-key":
        if "api_key" not in credentials.credentials:
            raise AuthenticationError("API key is required for x-api-key authentication")
        return AuthHeaders(headers={
            "x-api-key": credentials.credentials["api_key"],
            "Content-Type": "application/json"
        })
    
    raise AuthenticationError(f"Unsupported authentication type: {credentials.auth_type}") 