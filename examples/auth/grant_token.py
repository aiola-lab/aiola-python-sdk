import os
from aiola import AiolaClient

def grant_token():
    api_key = os.getenv("AIOLA_API_KEY")

    # Generate a temporary token from an API key.
    access_token = AiolaClient.grant_token(api_key=api_key)
    
    print(f"Token: {access_token[:50]}...")

    # Create a client with the temporary token.
    client = AiolaClient(access_token=access_token)

    print("Client created successfully with access token")


grant_token()