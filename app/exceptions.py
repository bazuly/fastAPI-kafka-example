from uuid import UUID


class BaseAppError(Exception):
    """Base exception for all application errors."""
    pass


class ApplicationNotFound(BaseAppError):
    """Exception raised when an application cannot be found."""

    def __init__(self, user_name: str = None):
        self.user_name = user_name
        message = f"Application for '{user_name}' not found." if user_name else "No available applications."
        super().__init__(message)


class ImageUploadError(Exception):
    """Base exception for all image upload errors."""
    pass


class ImageNotFoundError(ImageUploadError):
    """Exception raised when an image cannot be found."""

    def __init__(self, image_id: int | UUID):
        self.image_id = image_id
        super().__init__(f"Image not found. ID: {image_id}")


class DatabaseError(Exception):
    """Base exception for all database errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Exception raised when a database connection cannot be established."""

    def __init__(self, details: str = None):
        self.details = details
        message = "Failed to connect to database."
        if details:
            message += f" Details: {details}"
        super().__init__(message)


class RepositoryError(DatabaseError):
    """Default repository exception."""

    def __init__(self, message: str = "Repository error"):
        super().__init__(message)


class KafkaError(Exception):
    """Base exception for Kafka consumer/producer errors."""
    pass


class ConsumerError(KafkaError):
    def __init__(self, details: str = None):
        self.details = details
        message = "Failed to consume message, reload..."
        if details:
            message += f" Details: {details}"
        super().__init__(message)


class ProducerError(KafkaError):
    def __init__(self, details: str = None):
        self.details = details
        message = "Failed to produce message, reload..."
        if details:
            message += f" Details: {details}"
        super().__init__(message)
