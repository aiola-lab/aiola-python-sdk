class AiolaStreamingError(Exception):
    def __init__(self, message: str, details: dict = None):
        """
        Custom error class for Aiola Streaming-related exceptions.

        :param message: The error message
        :param details: Optional additional details about the error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        """
        Returns a string representation of the error.
        Includes the message and details if available.
        """
        base_message = f"AiolaStreamingError: {self.message}"
        if self.details:
            return f"{base_message} | Details: {self.details}"
        return base_message