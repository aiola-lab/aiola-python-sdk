from typing import Dict, Any
from ..models.auth import AuthHeaders, AuthCredentials
from ..exceptions import AuthenticationError

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
        return AuthHeaders(headers={
                "AUTHORIZATION": f"Bearer {credentials.credentials['token']}",
                "Content-Type": "application/json"
            })

    elif credentials.auth_type == "x-api-key":
        if "api_key" not in credentials.credentials:
            raise AuthenticationError("API key is required for x-api-key authentication")
        return AuthHeaders(headers={
            "x-api-key": credentials.credentials["api_key"],
            "Content-Type": "application/json"
        })

    raise AuthenticationError(f"Unsupported authentication type: {credentials.auth_type}")