"""
AI Chat Routes Module for Mobile App

Purpose:
    Provides REST API endpoints for mobile app chat UI to interact with
    AI chat service. Enables direct chat functionality without WhatsApp,
    using the same underlying chat_with_model function for consistency.

Dependencies:
    - fastapi: Web framework and routing
    - pydantic: Request/response validation
    - app.services.ai_chat: Core chat functionality
    - app.models.message_log_model: Message persistence
    - app.core.security: JWT authentication
    - app.db.mongodb: Database connection

Endpoints:
    POST /chat
        Accept chat message from mobile app
        Authenticate user via JWT token
        Process message through AI chat service
        Save user and bot messages to database
        Return AI response for display in app
        
Usage:
    # Send chat message from mobile app
    curl -X POST http://localhost:8000/api/v1/ai/chat \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer <jwt_token>" \
      -d '{
        "user_id": "usr_1234567890",
        "phone": "+919876543210",
        "metadata": {
          "name": "Rahul",
          "job": "Delivery Partner",
          "transaction_summary": {"balance": 12000}
        },
        "message": "How much did I spend on food this month?",
        "provider": "openai"
      }'

Reference:
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import logging

from app.services.ai_chat import chat_with_model
from app.models.message_log_model import create_message_doc, save_message
from app.core.security import get_current_user
from app.db.mongodb import get_db

# Logger for AI chat operations
logger = logging.getLogger("kivi.ai")

# Create router instance
router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class ChatRequest(BaseModel):
    """
    Chat request body schema for mobile app.
    
    Attributes:
        user_id: User identifier
        phone: User phone number
        metadata: User context dictionary (name, job, goals, transaction_summary)
        message: User's message text
        provider: AI provider to use ("openai" or "anthropic")
    """
    user_id: str = Field(..., description="User identifier", example="usr_1234567890")
    phone: str = Field(..., description="User phone number", example="+919876543210")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="User context metadata",
        example={
            "name": "Rahul Sharma",
            "job": "Delivery Partner",
            "gig_platforms": ["Swiggy", "Zomato"],
            "transaction_summary": {
                "balance": 12000.00,
                "monthly_spending": 22000.00
            }
        }
    )
    message: str = Field(..., description="User's message text", example="How much did I spend on food?")
    provider: str = Field(
        default="openai",
        description="AI provider name",
        example="openai"
    )


class ChatResponse(BaseModel):
    """
    Chat response schema for mobile app.
    
    Attributes:
        reply: AI-generated response text
        provider: AI provider used
        usage: Usage statistics (latency, token counts)
        message_id: ID of the bot message saved to database
    """
    reply: str = Field(..., description="AI-generated response")
    provider: str = Field(..., description="AI provider used")
    usage: Dict[str, Any] = Field(..., description="Usage statistics")
    message_id: str = Field(..., description="Bot message ID")


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    db: Any = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ChatResponse:
    """
    Process chat message from mobile app and return AI response.
    
    This endpoint provides the same chat functionality as WhatsApp but
    through a REST API for mobile app integration. It authenticates the
    user via JWT, processes the message through the AI chat service,
    persists both user and bot messages, and returns the response.
    
    Workflow:
    1. Authenticate user via JWT token
    2. Validate request parameters
    3. Save user message to database
    4. Call chat_with_model() with metadata and message
    5. Save bot response to database
    6. Return AI response to mobile app
    
    Args:
        request: Chat request with user_id, phone, metadata, message, provider
        db: Database instance (injected dependency)
        current_user: Authenticated user info from JWT (injected dependency)
    
    Returns:
        ChatResponse with AI reply, provider, usage stats, and message_id
    
    Raises:
        HTTPException 400: If request validation fails
        HTTPException 401: If authentication fails
        HTTPException 500: If AI chat or database operation fails
    
    Example Request:
        POST /api/v1/ai/chat
        Headers:
            Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
            Content-Type: application/json
        Body:
        {
            "user_id": "usr_1234567890",
            "phone": "+919876543210",
            "metadata": {
                "name": "Rahul",
                "job": "Delivery Partner",
                "transaction_summary": {"balance": 12000}
            },
            "message": "How much did I spend on food this month?",
            "provider": "openai"
        }
    
    Example Response:
        {
            "reply": "Based on your transaction history, you spent ₹3,200 on food this month.",
            "provider": "openai",
            "usage": {
                "latency_ms": 1250,
                "prompt_length": 450,
                "response_length": 85
            },
            "message_id": "msg_1234567890_20250121143022123456"
        }
    """
    logger.info(f"Chat request from user {request.user_id} via mobile app")
    logger.debug(f"Message: {request.message[:100]}...")
    logger.debug(f"Provider: {request.provider}")
    
    # Verify authenticated user matches request user_id
    if current_user["user_id"] != request.user_id:
        logger.warning(
            f"User ID mismatch: JWT user_id={current_user['user_id']}, "
            f"request user_id={request.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID in request does not match authenticated user"
        )
    
    try:
        # Step 1: Save user message to database
        logger.debug(f"Creating user message document for {request.user_id}")
        user_message_doc = create_message_doc(
            user_id=request.user_id,
            phone=request.phone,
            metadata=request.metadata,
            role="user",
            text=request.message,
            model=None
        )
        
        await save_message(db, user_message_doc)
        logger.info(f"Saved user message: {user_message_doc['message_id']}")
        
        # Step 2: Call chat_with_model() to get AI response
        logger.debug(f"Calling chat_with_model with provider={request.provider}")
        ai_response = await chat_with_model(
            metadata=request.metadata,
            message=request.message,
            provider=request.provider
        )
        
        logger.info(
            f"Received AI response from {ai_response['provider']} "
            f"(latency: {ai_response['usage']['latency_ms']}ms)"
        )
        
        # Step 3: Save bot message to database
        logger.debug(f"Creating bot message document for {request.user_id}")
        bot_message_doc = create_message_doc(
            user_id=request.user_id,
            phone=request.phone,
            metadata=request.metadata,
            role="bot",
            text=ai_response["reply"],
            model=ai_response["provider"]
        )
        
        await save_message(db, bot_message_doc)
        logger.info(f"Saved bot message: {bot_message_doc['message_id']}")
        
        # Step 4: Return AI response to mobile app
        return ChatResponse(
            reply=ai_response["reply"],
            provider=ai_response["provider"],
            usage=ai_response["usage"],
            message_id=bot_message_doc["message_id"]
        )
    
    except ValueError as e:
        # Handle validation errors (e.g., invalid provider)
        logger.error(f"Validation error in chat request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(
            f"Error processing chat request for user {request.user_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat request: {str(e)}"
        )


# Health check endpoint for AI service
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """
    Health check endpoint for AI chat service.
    
    Returns:
        dict: Service status information
    
    Example:
        GET /api/v1/ai/health
        
        Response:
        {
            "status": "healthy",
            "service": "ai-chat",
            "providers": ["openai", "anthropic"]
        }
    """
    return {
        "status": "healthy",
        "service": "ai-chat",
        "providers": ["openai", "anthropic"]
    }
