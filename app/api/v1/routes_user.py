"""
User Profile Routes Module

Purpose:
    Provides endpoints for retrieving and updating authenticated user profiles.
    Handles user profile management with validation and database persistence.

Dependencies:
    - fastapi: Web framework and routing
    - pydantic: Request/response validation
    - app.core.security: Authentication dependency (get_current_user)
    - app.models.user_model: User data access and validation
    - app.db.mongodb: Database connection

Endpoints:
    GET /users/me
        Retrieve authenticated user's profile
        Requires: Authorization Bearer token
        Returns: Complete user profile with financial data
        
        Response (200 OK):
            {
                "user_id": "usr_9876543210",
                "phone": "+919876543210",
                "name": "Rahul Sharma",
                "email": "rahul@example.com",
                "job": "Delivery Partner",
                "city": "Mumbai",
                "gig_platforms": ["Swiggy", "Zomato", "Dunzo"],
                "financial_summary": {...},
                "budgets": [...],
                "goals": [...],
                "notification_preferences": {...},
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-20T14:22:00Z"
            }
    
    PUT /users/me
        Update authenticated user's profile
        Requires: Authorization Bearer token
        Request Body: Partial or complete user profile fields
        Returns: Updated user profile
        
        Request Body (partial update example):
            {
                "name": "Rahul Kumar Sharma",
                "city": "Pune",
                "job": "Freelance Designer"
            }
        
        Response (200 OK):
            {
                "user_id": "usr_9876543210",
                "phone": "+919876543210",
                "name": "Rahul Kumar Sharma",
                ...
            }

Usage:
    # Get current user profile
    curl -X GET http://localhost:8000/api/v1/users/me \
      -H "Authorization: Bearer <access_token>"
    
    # Update user profile
    curl -X PUT http://localhost:8000/api/v1/users/me \
      -H "Authorization: Bearer <access_token>" \
      -H "Content-Type: application/json" \
      -d '{"name": "New Name", "city": "Pune"}'

Reference:
    Requirements: 6.1, 6.2, 6.5
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from app.core.security import get_current_user
from app.models.user_model import (
    get_user_by_phone,
    upsert_user,
    UserProfile,
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


class UserUpdateRequest(BaseModel):
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
    financial_summary: Optional[Dict[str, Any]] = Field(None, description="Financial summary data")
    budgets: Optional[List[Dict[str, Any]]] = Field(None, description="Budget configurations")
    goals: Optional[List[Dict[str, Any]]] = Field(None, description="Financial goals")
    notification_preferences: Optional[Dict[str, Any]] = Field(None, description="Notification settings")


@router.get("/users/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
) -> UserProfile:
    """
    Retrieve authenticated user's profile.
    
    Returns complete user profile including financial summary, budgets,
    goals, and notification preferences. Requires valid JWT token in
    Authorization header.
    
    Args:
        current_user: Authenticated user info from JWT token (injected)
        db: Database instance (injected dependency)
    
    Returns:
        UserProfile with all user data
    
    Raises:
        HTTPException 401: If authentication fails (handled by dependency)
        HTTPException 404: If user profile not found in database
        HTTPException 500: If database operation fails
    
    Example:
        GET /api/v1/users/me
        Headers: Authorization: Bearer <token>
        
        Response:
        {
            "user_id": "usr_9876543210",
            "phone": "+919876543210",
            "name": "Rahul Sharma",
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
            logger.error(f"User profile not found for user_id: {user_id}, phone: {phone}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        logger.info(f"Successfully retrieved profile for user: {user_id}")
        
        # Convert MongoDB document to UserProfile model
        # Remove MongoDB _id field if present
        if "_id" in user:
            del user["_id"]
        
        return UserProfile(**user)
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Log unexpected errors and return 500
        logger.error(f"Error fetching profile for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching user profile"
        )


@router.put("/users/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def update_user_profile(
    update_data: UserUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
) -> UserProfile:
    """
    Update authenticated user's profile.
    
    Accepts partial updates - only provided fields will be updated.
    Validates request body with Pydantic model and persists changes
    to database. Automatically updates the updated_at timestamp.
    
    Args:
        update_data: User profile fields to update
        current_user: Authenticated user info from JWT token (injected)
        db: Database instance (injected dependency)
    
    Returns:
        Updated UserProfile with all user data
    
    Raises:
        HTTPException 401: If authentication fails (handled by dependency)
        HTTPException 404: If user profile not found in database
        HTTPException 422: If validation fails (handled by Pydantic)
        HTTPException 500: If database operation fails
    
    Example:
        PUT /api/v1/users/me
        Headers: Authorization: Bearer <token>
        Body:
        {
            "name": "Rahul Kumar Sharma",
            "city": "Pune",
            "job": "Freelance Designer"
        }
        
        Response:
        {
            "user_id": "usr_9876543210",
            "phone": "+919876543210",
            "name": "Rahul Kumar Sharma",
            "city": "Pune",
            "job": "Freelance Designer",
            ...
        }
    """
    user_id = current_user["user_id"]
    phone = current_user["phone"]
    
    logger.info(f"Updating profile for user: {user_id}")
    
    try:
        # Step 1: Get existing user profile
        existing_user = await get_user_by_phone(db, phone)
        
        if not existing_user:
            logger.error(f"User profile not found for user_id: {user_id}, phone: {phone}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Step 2: Build update dictionary with only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            # No fields to update, return existing profile
            logger.info(f"No fields to update for user: {user_id}")
            if "_id" in existing_user:
                del existing_user["_id"]
            return UserProfile(**existing_user)
        
        logger.debug(f"Updating fields for user {user_id}: {list(update_dict.keys())}")
        
        # Step 3: Merge update data with existing user data
        # Start with existing user data
        updated_user_data = existing_user.copy()
        
        # Update with new values
        for key, value in update_dict.items():
            updated_user_data[key] = value
        
        # Ensure phone and user_id are preserved
        updated_user_data["phone"] = phone
        updated_user_data["user_id"] = user_id
        
        # Step 4: Persist updated profile to database
        updated_user = await upsert_user(db, updated_user_data)
        
        logger.info(f"Successfully updated profile for user: {user_id}")
        
        # Step 5: Return updated profile
        if "_id" in updated_user:
            del updated_user["_id"]
        
        return UserProfile(**updated_user)
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Log unexpected errors and return 500
        logger.error(f"Error updating profile for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating user profile"
        )
