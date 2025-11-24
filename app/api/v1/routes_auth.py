"""
Authentication Routes Module

Purpose:
    Provides authentication endpoints for user login and JWT token generation.
    Handles credential validation and token issuance for accessing protected
    endpoints throughout the KIVI Backend system.

Dependencies:
    - fastapi: Web framework and routing
    - pydantic: Request/response validation
    - app.core.security: JWT token creation
    - app.models.user_model: User data access
    - app.db.mongodb: Database connection

Endpoints:
    POST /login
        Accept phone and password in request body
        Validate credentials (mock validation for hackathon)
        Generate JWT token using create_token()
        Return access_token and token_type in response
        
        Request Body:
            {
                "phone": "+919876543210",
                "password": "demo123"
            }
        
        Response (200 OK):
            {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": "usr_9876543210",
                "phone": "+919876543210"
            }
        
        Response (401 Unauthorized):
            {
                "detail": "Invalid credentials"
            }

Usage:
    # Login request
    curl -X POST http://localhost:8000/api/v1/login \
      -H "Content-Type: application/json" \
      -d '{"phone": "+919876543210", "password": "demo123"}'
    
    # Use token in subsequent requests
    curl -X GET http://localhost:8000/api/v1/users/me \
      -H "Authorization: Bearer <access_token>"

Reference:
    Requirements: 5.1, 5.2
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Any
import logging

from app.core.security import create_token
from app.core.response_models import success_response, error_response, ResponseCode
from app.models.user_model import get_user_by_phone, upsert_user, create_empty_user
from app.db.mongodb import get_db
from app.services.aa_service import fetch_aa_data, normalize_aa_data
from app.services.whatsapp_service import send_whatsapp_text

# Logger for authentication operations
logger = logging.getLogger("kivi.auth")

# Create router instance
router = APIRouter(prefix="/api/v1", tags=["authentication"])


class LoginRequest(BaseModel):
    """
    Login request body schema.
    
    Attributes:
        phone: User phone number with country code (e.g., "+919876543210")
        password: User password (mock validation for hackathon)
    """
    phone: str = Field(..., description="Phone number with country code", example="+919876543210")
    password: str = Field(..., description="User password", example="demo123")


class LoginData(BaseModel):
    """
    Login response data schema.
    
    Attributes:
        access_token: JWT token for authentication
        token_type: Token type (always "bearer")
        user_id: Unique user identifier
        phone: User phone number
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: str = Field(..., description="User ID")
    phone: str = Field(..., description="User phone number")


def validate_credentials(phone: str, password: str) -> bool:
    """
    Validate user credentials.
    
    TODO: Implement proper authentication:
    - Hash the password and compare with stored hash
    - Implement rate limiting for failed attempts
    - Add account lockout after multiple failures
    - Log authentication attempts
    
    Args:
        phone: User phone number
        password: User password
    
    Returns:
        True if credentials are valid, False otherwise
    """
    logger.debug(f"Validating credentials for phone: {phone}")
    
    # Default password for all users: dummy@123
    # TODO: Implement proper password validation with hashing
    if password == "dummy@123":
        logger.info(f"Valid credentials for phone: {phone}")
        return True
    
    logger.warning(f"Invalid password for phone: {phone}")
    return False


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    db: Any = Depends(get_db)
) -> dict:
    """
    Authenticate user and generate JWT token.
    
    Validates user credentials (mock validation for hackathon) and returns
    a JWT access token for accessing protected endpoints. If the user doesn't
    exist in the database, creates a new user profile with sample gig worker data.
    
    Args:
        request: Login request containing phone and password
        db: Database instance (injected dependency)
    
    Returns:
        LoginResponse with access_token, token_type, user_id, and phone
    
    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 500: If database operation fails
    
    Example:
        POST /api/v1/login
        {
            "phone": "+919876543210",
            "password": "demo123"
        }
        
        Response:
        {
            "access_token": "eyJhbGc...",
            "token_type": "bearer",
            "user_id": "usr_9876543210",
            "phone": "+919876543210"
        }
    """
    logger.info(f"Login attempt for phone: {request.phone}")
    
    try:
        # Step 1: Validate credentials
        if not validate_credentials(request.phone, request.password):
            logger.warning(f"Failed login attempt for phone: {request.phone}")
            return error_response(
                message="Invalid phone number or password",
                code=ResponseCode.INVALID_CREDENTIALS,
                error_type="AuthenticationError",
                details="Please check your credentials and try again"
            )
        
        # Step 2: Get or create user profile
        user = await get_user_by_phone(db, request.phone)
        
        is_first_time_user = False
        if not user:
            # First-time user: create minimal profile
            is_first_time_user = True
            logger.info(f"First-time login for {request.phone}, creating user profile")
            new_user = create_empty_user(request.phone)
            user = await upsert_user(db, new_user)
            logger.info(f"Created new user profile: {user['user_id']}")
        else:
            logger.info(f"Existing user login: {user['user_id']}")
        
        # Step 3: Onboarding flow for first-time users
        if is_first_time_user:
            logger.info(f"Starting onboarding flow for new user: {user['user_id']}")
            
            # Step 3a: Fetch and populate Account Aggregator data
            try:
                logger.debug(f"Fetching AA data for user: {user['user_id']}")
                aa_data = await fetch_aa_data(user['user_id'])
                
                # Normalize AA data to internal format
                normalized_aa = normalize_aa_data(aa_data)
                
                # Update user profile with AA financial data
                user['financial_summary'] = normalized_aa['financial_summary']
                
                # Store AA data in user metadata for future reference
                if 'metadata' not in user:
                    user['metadata'] = {}
                user['metadata']['aa_data_fetched'] = True
                user['metadata']['aa_last_sync'] = normalized_aa['metadata'].get('fetch_timestamp')
                
                # Update user in database with AA data
                user = await upsert_user(db, user)
                logger.info(f"Updated user profile with AA data: {len(normalized_aa['transactions'])} transactions")
                
            except Exception as e:
                # Log error but don't fail onboarding if AA data fetch fails
                logger.error(f"Failed to fetch AA data during onboarding: {e}", exc_info=True)
                logger.warning("Continuing onboarding without AA data")
            
            # Step 3b: Send welcome WhatsApp message
            try:
                welcome_message = _build_welcome_message(user)
                logger.debug(f"Sending welcome message to {phone}")
                
                send_result = await send_whatsapp_text(phone, welcome_message)
                
                if send_result.get("status") == "success":
                    logger.info(f"Welcome message sent successfully to {phone}")
                else:
                    logger.warning(f"Failed to send welcome message: {send_result.get('error')}")
                
            except Exception as e:
                # Log error but don't fail onboarding if WhatsApp message fails
                logger.error(f"Failed to send welcome message: {e}", exc_info=True)
                logger.warning("Continuing onboarding without welcome message")
            
            logger.info(f"Onboarding completed for user: {user['user_id']}")
        
        # Step 4: Generate JWT token
        user_id = user["user_id"]
        phone = user["phone"]
        
        access_token = create_token(user_id, phone)
        logger.info(f"Generated access token for user: {user_id}")
        
        # Step 5: Return response
        return success_response(
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user_id,
                "phone": phone
            },
            message="Login successful",
            code=ResponseCode.SUCCESS
        )
    
    except Exception as e:
        # Log unexpected errors and return 500
        logger.error(f"Login error for phone {request.phone}: {e}", exc_info=True)
        return error_response(
            message="An error occurred during login",
            code=ResponseCode.INTERNAL_ERROR,
            error_type="InternalError",
            details=str(e) if logger.level == logging.DEBUG else None
        )


def _build_welcome_message(user: dict) -> str:
    """
    Build personalized welcome message for first-time users.
    
    Args:
        user: User profile dictionary
    
    Returns:
        Welcome message text
    """
    name = user.get("name", "there")
    
    message_parts = [
        f"Hi {name}! 👋",
        "",
        "Welcome to KIVI - your AI-powered financial companion! 🎉",
        "",
        "I'm here to help you manage your finances, track your earnings, and achieve your financial goals.",
        "",
        "Here's what I can help you with:",
        "💰 Track income from multiple sources",
        "📊 Analyze spending patterns",
        "🎯 Set and monitor financial goals",
        "💡 Get personalized financial insights",
        "⚠️ Receive smart alerts and nudges",
        "",
        "Just send me a message anytime!",
        "",
        "Let's get started! 🚀"
    ]
    
    return "\n".join(message_parts)
