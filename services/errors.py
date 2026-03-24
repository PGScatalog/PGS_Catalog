class NotFoundError(Exception):
    """Exception raised when a resource is not found in an API."""
    def __init__(self, message):
        super().__init__(message)
