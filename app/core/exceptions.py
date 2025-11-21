"""
Custom Exception Classes

Purpose:
    Define custom exception classes for the KIVI Backend system.
    Provides structured error handling with specific exception types
    for different failure scenarios.

Dependencies:
    - fastapi: HTTP exception handling

Usage:
    from app.core.exceptions import AuthenticationError, WhatsAppAPIError
    
    if not valid_token:
        raise AuthenticationError("Invalid token")
    
    if api_call_failed:
        raise WhatsAppAPIError("Failed to send message")
"""

from fastapi import HTTPException, status


class KiviException(Exception):
    """Base exception for KIVI system."""
    
    def __init__(self, message: str = "An error occurred in KIVI system"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(KiviException):
    """Authentication failed."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(KiviException):
    """Authorization failed - user doesn't have permission."""
    
    def __init__(self, message: str = "Authorization failed"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    """JWT token is invalid."""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)


class WhatsAppAPIError(KiviException):
    """WhatsApp API call failed."""
    
    def __init__(self, message: str = "WhatsApp API call failed"):
        super().__init__(message)


class AIProviderError(KiviException):
    """AI provider call failed."""
    
    def __init__(self, message: str = "AI provider call failed", provider: str = None):
        self.provider = provider
        if provider:
            message = f"{message} (provider: {provider})"
        super().__init__(message)


class DatabaseError(KiviException):
    """Database operation failed."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message)


class ValidationError(KiviException):
    """Data validation failed."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message)


class NotFoundError(KiviException):
    """Resource not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message)


def kivi_exception_to_http(exc: KiviException) -> HTTPException:
    """
    Convert KIVI custom exceptions to FastAPI HTTPException.
    
    Args:
        exc: KIVI custom exception
        
    Returns:
        HTTPException with appropriate status code
    """
    if isinstance(exc, (AuthenticationError, TokenExpiredError, InvalidTokenError)):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    elif isinstance(exc, AuthorizationError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.message
        )
    elif isinstance(exc, NotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message
        )
    elif isinstance(exc, ValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message
        )
