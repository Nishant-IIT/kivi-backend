"""
User Profile Routes Module

Purpose:
    Provides endpoints for user profile management including retrieval
    and updates. All endpoints require JWT authentication via the
    get_current_user dependency.

Dependencies:
    - fastapi: Web framework and routing
    - pydantic: Request/response validation
    - app.core.security: Authentication dependency
    - app.models.user_model: User data access and validation
    - app.db.mongodb: Database connection

Endpoints:
    GET /users/me
        Retrieve authenticated user's profile
        Requires: Authorization header with Bearer token
        Returns: Complete user profile with financial data
        
        Response (200 OK):
            {
                "user_id": "usr_9876543210",
                "phone": "+919876543210",
                "name": "Rahul Sharma",
                "email": "rahul@example.com",
                "job": "Delivery Partner",
                "city": "Mumbai",
                "gig_platforms": ["Swiggy", "Zomato"],
                "financial_summary": {...},
                "budgets": [...],
                "goals": [...],
                "notification_preferences": {...},
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-20T14:22:00Z"
            }
    
    PUT /users/me
        Update authenticated user's profile
        Requires: Authorization header with Bearer token
        Request Body: Partial or complete user profile fields
        Returns: Updated user profile
        
        Request Body:
            {
                "name": "Rahul Kumar",
                "city": "Delhi",
                "job": "Freelance Designer",
                "gig_platforms": ["Upwork", "Fiverr"]
            }
        
        Response (200 OK):
            {
                "user_id": "usr_9876543210",
                "phone": "+919876543210",
                "name": "Rahul Kumar",
                ...
            }

Usage:
    # Get user profile
    curl -X GET http://localhost:8000/api/v1/users/me \
      -H "Authorization: Bearer <access_token>"
    
    # Update user profile
    curl -X PUT http://localhost:8000/api/v1/users/me \
      -H "Authorization: Bearer <access_token>" \
      -H "Content-Type: application/json" \
      -d '{"name": "New Name", "city": "Delhi"}'

Reference:
    Requirements: 6.1, 6.2, 6.5
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from app.core.security import get_current_user
from app.core.response_models import success_response, error_response, ResponseCode
from app.models.user_model import (
    UserProfile,
    get_user_by_phone,
    upsert_user,
    FinancialSummary,
    Budget,
    Goal,
    NotificationPreferences
)
from app.db.mongodb import get_db

# Logger for user profile operations
logger = logging.getLogger("kivi.user")

# Create router instance
router = APIRouter(prefix="/api/v1", tags=["user"])


class UserProfileUpdateRequest(BaseModel):
    """
    User profile update request schema.
    
    All fields are optional to support partial updates.
    Only provided fields will be updated in the database.
    
    Attributes:
        name: User's full name
        email: User's email address
        job: User's job title or occupation
        city: User's city of residence
        gig_platforms: List of gig platforms user works on
        financial_summary: Financial summary data
        budgets: List of budget configurations
        goals: List of financial goals
        notification_preferences: Notification settings
    """
    name: Optional[str] = Field(None, description="User's full name", example="Rahul Sharma")
    email: Optional[str] = Field(None, description="User's email address", example="rahul@example.com")
    job: Optional[str] = Field(None, description="User's job title", example="Delivery Partner")
    city: Optional[str] = Field(None, description="User's city", example="Mumbai")
    gig_platforms: Optional[List[str]] = Field(None, description="List of gig platforms", example=["Swiggy", "Zomato"])
    financial_summary: Optional[FinancialSummary] = Field(None, description="Financial summary data")
    budgets: Optional[List[Budget]] = Field(None, description="Budget configurations")
    goals: Optional[List[Goal]] = Field(None, description="Financial goals")
    notification_preferences: Optional[NotificationPreferences] = Field(None, description="Notification settings")


@router.get("/users/me", status_code=status.HTTP_200_OK)
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
) -> dict:
    """
    Retrieve authenticated user's profile.
    
    Returns complete user profile including financial summary, budgets,
    goals, and notification preferences. Requires valid JWT token in
    Authorization header.
    
    Args:
        current_user: Authenticated user info from JWT token (injected)
        db: Database instance (injected dependency)
    
    Returns:
        UserProfile: Complete user profile data
    
    Raises:
        HTTPException 401: If authentication fails (handled by dependency)
        HTTPException 404: If user profile not found in database
        HTTPException 500: If database operation fails
    
    Example:
        GET /api/v1/users/me
        Headers: Authorization: Bearer eyJhbGc...
        
        Response:
        {
            "user_id": "usr_9876543210",
            "phone": "+919876543210",
            "name": "Rahul Sharma",
            "job": "Delivery Partner",
            ...
        }
    """
    user_id = current_user["user_id"]
    phone = current_user["phone"]
    
    logger.info(f"Fetching profile for user: {user_id}")
    
    try:
        # Retrieve user from database by phone
        user = await get_user_by_phone(db, phone)
        
        if not user:
            logger.warning(f"User profile not found for user_id: {user_id}, phone: {phone}")
            return error_response(
                message="User profile not found",
                code=ResponseCode.NOT_FOUND,
                error_type="NotFoundError",
                details=f"No profile found for user {user_id}"
            )
        
        logger.info(f"Successfully retrieved profile for user: {user_id}")
        
        # Return user profile
        return success_response(
            data=user,
            message="User profile retrieved successfully",
            code=ResponseCode.SUCCESS
        )
    
    except Exception as e:
        # Log unexpected errors and return 500
        logger.error(f"Error fetching profile for user {user_id}: {e}", exc_info=True)
        return error_response(
            message="Failed to retrieve user profile",
            code=ResponseCode.DATABASE_ERROR,
            error_type="DatabaseError",
            details=str(e) if logger.level == logging.DEBUG else None
        )


@router.put("/users/me", status_code=status.HTTP_200_OK)
async def update_user_profile(
    update_data: UserProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
) -> dict:
    """
    Update authenticated user's profile.
    
    Accepts partial or complete profile updates. Only provided fields
    will be updated in the database. Validates request body with Pydantic
    models and updates the user profile in the database.
    
    Args:
        update_data: Profile update data (partial updates supported)
        current_user: Authenticated user info from JWT token (injected)
        db: Database instance (injected dependency)
    
    Returns:
        UserProfile: Updated user profile data
    
    Raises:
        HTTPException 401: If authentication fails (handled by dependency)
        HTTPException 404: If user profile not found in database
        HTTPException 422: If validation fails (handled by Pydantic)
        HTTPException 500: If database operation fails
    
    Example:
        PUT /api/v1/users/me
        Headers: Authorization: Bearer eyJhbGc...
        Body:
        {
            "name": "Rahul Kumar",
            "city": "Delhi",
            "gig_platforms": ["Uber", "Ola"]
        }
        
        Response:
        {
            "user_id": "usr_9876543210",
            "phone": "+919876543210",
            "name": "Rahul Kumar",
            "city": "Delhi",
            "gig_platforms": ["Uber", "Ola"],
            ...
        }
    """
    user_id = current_user["user_id"]
    phone = current_user["phone"]
    
    logger.info(f"Updating profile for user: {user_id}")
    
    try:
        # Step 1: Retrieve existing user profile
        existing_user = await get_user_by_phone(db, phone)
        
        if not existing_user:
            logger.warning(f"User profile not found for user_id: {user_id}, phone: {phone}")
            return error_response(
                message="User profile not found",
                code=ResponseCode.NOT_FOUND,
                error_type="NotFoundError",
                details=f"No profile found for user {user_id}"
            )
        
        # Step 2: Build update dictionary with only provided fields
        update_dict = {}
        
        # Convert Pydantic model to dict, excluding unset fields
        update_fields = update_data.model_dump(exclude_unset=True)
        
        # Log which fields are being updated
        if update_fields:
            logger.debug(f"Updating fields for user {user_id}: {list(update_fields.keys())}")
        else:
            logger.info(f"No fields to update for user {user_id}")
        
        # Merge update fields with existing user data
        for key, value in update_fields.items():
            # Convert nested Pydantic models to dicts
            if isinstance(value, BaseModel):
                update_dict[key] = value.model_dump()
            elif isinstance(value, list) and value and isinstance(value[0], BaseModel):
                update_dict[key] = [item.model_dump() for item in value]
            else:
                update_dict[key] = value
        
        # Preserve user_id and phone (cannot be changed)
        update_dict["user_id"] = existing_user["user_id"]
        update_dict["phone"] = existing_user["phone"]
        
        # Preserve created_at timestamp
        if "created_at" in existing_user:
            update_dict["created_at"] = existing_user["created_at"]
        
        # Step 3: Update user in database
        updated_user = await upsert_user(db, update_dict)
        
        logger.info(f"Successfully updated profile for user: {user_id}")
        
        # Return updated user profile
        return success_response(
            data=updated_user,
            message="User profile updated successfully",
            code=ResponseCode.UPDATED
        )
    
    except Exception as e:
        # Log unexpected errors and return 500
        logger.error(f"Error updating profile for user {user_id}: {e}", exc_info=True)
        return error_response(
            message="Failed to update user profile",
            code=ResponseCode.DATABASE_ERROR,
            error_type="DatabaseError",
            details=str(e) if logger.level == logging.DEBUG else None
        )
