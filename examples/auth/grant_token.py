import os
from aiola import AiolaClient

def example():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )

        access_token = result.accessToken
        session_id = result.sessionId

        print(f"Access Token: {access_token}")
        print(f"Session ID: {session_id}")

        # Step 2: Create client
        client = AiolaClient(
            access_token=access_token
        )

        print("Client created successfully with access token")

        # Step 3: Use client for API calls (example usage)
        # You can now use the client for STT/TTS operations
        print("Client is ready for API operations")

        # Step 4: Close session when done
        close_result = AiolaClient.close_session(access_token)
        print(f"Session closed at: {close_result.deletedAt}")
        print(f"Status: {close_result.status}")

    except Exception as error:
        print('Error:', error)

if __name__ == "__main__":
    example()
