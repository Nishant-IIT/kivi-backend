"""
Standard API Response Models

Purpose:
    Provides standardized response structures for all API endpoints.
    Ensures consistent response format across the entire application.

Response Format:
    {
        "success": true/false,
        "code": "SUCCESS" or error code,
        "message": "Human readable message",
        "data": {...} or null,
        "error": {...} or null
    }
"""

from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class ErrorDetail(BaseModel):
    """Error detail structure."""
    type: str = Field(..., description="Error type")
    details: Optional[str] = Field(None, description="Additional error details")


class StandardResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper.
    
    All API endpoints should return responses in this format for consistency.
    """
    success: bool = Field(..., description="Whether the request was successful")
    code: str = Field(..., description="Response code (SUCCESS or error code)")
    message: str = Field(..., description="Human-readable message")
    data: Optional[T] = Field(None, description="Response data (null on error)")
    error: Optional[ErrorDetail] = Field(None, description="Error details (null on success)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "code": "SUCCESS",
                "message": "Operation completed successfully",
                "data": {"key": "value"},
                "error": None
            }
        }


# Response code constants
class ResponseCode:
    """Standard response codes."""
    # Success codes
    SUCCESS = "SUCCESS"
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    
    # Client error codes (4xx)
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    
    # Server error codes (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    WHATSAPP_SERVICE_ERROR = "WHATSAPP_SERVICE_ERROR"


def success_response(
    data: Any,
    message: str = "Operation completed successfully",
    code: str = ResponseCode.SUCCESS
) -> dict:
    """
    Create a success response.
    
    Args:
        data: Response data
        message: Success message
        code: Response code
    
    Returns:
        Standardized success response dictionary
    """
    return {
        "success": True,
        "code": code,
        "message": message,
        "data": data,
        "error": None
    }


def error_response(
    message: str,
    code: str = ResponseCode.INTERNAL_ERROR,
    error_type: str = "Error",
    details: Optional[str] = None
) -> dict:
    """
    Create an error response.
    
    Args:
        message: Error message
        code: Error code
        error_type: Type of error
        details: Additional error details
    
    Returns:
        Standardized error response dictionary
    """
    return {
        "success": False,
        "code": code,
        "message": message,
        "data": None,
        "error": {
            "type": error_type,
            "details": details
        }
    }
