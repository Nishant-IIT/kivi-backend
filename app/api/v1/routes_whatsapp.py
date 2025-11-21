"""
WhatsApp Webhook Routes Module

Purpose:
    Provides webhook endpoints for Meta WhatsApp Cloud API integration and
    notification sending capabilities. Handles incoming WhatsApp messages,
    processes them through the AI chat service, and sends outbound notifications.

Dependencies:
    - fastapi: Web framework and routing
    - pydantic: Request/response validation
    - app.services.whatsapp_service: WhatsApp message handling
    - app.models.message_log_model: Message persistence
    - app.db.mongodb: Database connection

Endpoints:
    POST /webhook
        Receive incoming WhatsApp messages from Meta Cloud API
        Process messages and respond with AI-generated replies
        Returns 200 OK quickly for webhook acknowledgment
        
    POST /send_notification
        Send proactive WhatsApp notifications to users
        Accepts phone, text, and optional provider parameters
        Persists outbound message to database
        
Usage:
    # Webhook endpoint (called by Meta)
    POST /api/v1/whatsapp/webhook
    
    # Send notification
    curl -X POST http://localhost:8000/api/v1/whatsapp/send_notification \
      -H "Content-Type: application/json" \
      -d '{
        "phone": "+919876543210",
        "text": "Your food budget is 80% spent this month.",
        "provider": "openai"
      }'

Reference:
    Requirements: 1.1, 1.5, 8.1, 8.2, 8.4
"""

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any, Optional
import logging

from app.services.whatsapp_service import handle_incoming_webhook, send_whatsapp_text
from app.models.message_log_model import create_message_doc, save_message
from app.db.mongodb import get_db

# Logger for webhook operations
logger = logging.getLogger("kivi.webhook")

# Create router instance
router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])


class SendNotificationRequest(BaseModel):
    """
    Send notification request body schema.
    
    Attributes:
        phone: Recipient phone number with country code
        text: Message text to send
        provider: AI provider name for context (optional)
    """
    phone: str = Field(..., description="Recipient phone number", example="+919876543210")
    text: str = Field(..., description="Message text", example="Your food budget is 80% spent.")
    provider: Optional[str] = Field(default="openai", description="AI provider name")


class SendNotificationResponse(BaseModel):
    """
    Send notification response schema.
    
    Attributes:
        status: Operation status ("success" or "error")
        message_id: WhatsApp message ID if successful
        error: Error message if failed
    """
    status: str = Field(..., description="Operation status")
    message_id: Optional[str] = Field(None, description="WhatsApp message ID")
    error: Optional[str] = Field(None, description="Error message if failed")


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook(
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db)
) -> dict:
    """
    Receive and process incoming WhatsApp messages from Meta Cloud API.
    
    This endpoint is called by Meta's WhatsApp Cloud API when a user sends
    a message. It quickly acknowledges the webhook (200 OK) and processes
    the message in the background to avoid timeout issues.
    
    Workflow:
    1. Receive webhook payload from Meta
    2. Return 200 OK immediately for acknowledgment
    3. Process message in background:
       - Extract phone, user_id, message
       - Get user profile for context
       - Persist user message
       - Generate AI response
       - Persist bot message
       - Send reply via WhatsApp
    
    Args:
        payload: Meta webhook payload (JSON)
        background_tasks: FastAPI background tasks for async processing
        db: Database instance (injected dependency)
    
    Returns:
        dict: Simple acknowledgment response
    
    Example Payload:
        {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "919876543210",
                            "text": {"body": "How much did I spend?"},
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
    
    Example Response:
        {
            "status": "received"
        }
    """
    logger.info("Received WhatsApp webhook request")
    logger.debug(f"Webhook payload: {payload}")
    
    # Add message processing to background tasks
    # This allows us to return 200 OK immediately
    background_tasks.add_task(
        handle_incoming_webhook,
        db,
        payload
    )
    
    logger.info("Webhook acknowledged, processing in background")
    
    # Return quick acknowledgment
    return {"status": "received"}


@router.post("/send_notification", response_model=SendNotificationResponse, status_code=status.HTTP_200_OK)
async def send_notification(
    request: SendNotificationRequest,
    db: Any = Depends(get_db)
) -> SendNotificationResponse:
    """
    Send proactive WhatsApp notification to user.
    
    Sends a WhatsApp message to the specified phone number and persists
    the outbound message to the database for conversation tracking.
    Used for sending budget alerts, spending insights, and other notifications.
    
    Args:
        request: Notification request with phone, text, and provider
        db: Database instance (injected dependency)
    
    Returns:
        SendNotificationResponse with status and message_id or error
    
    Raises:
        HTTPException 500: If message sending or persistence fails
    
    Example:
        POST /api/v1/whatsapp/send_notification
        {
            "phone": "+919876543210",
            "text": "You've exceeded your food budget by ₹200.",
            "provider": "openai"
        }
        
        Response:
        {
            "status": "success",
            "message_id": "wamid.HBgNOTE5ODc2NTQzMjEwFQIAERgSMDhBRjE2QjdGNzY4QzQ5OTJBAA=="
        }
    """
    logger.info(f"Send notification request for phone: {request.phone}")
    logger.debug(f"Message text: {request.text[:100]}...")
    
    try:
        # Step 1: Send WhatsApp message
        send_result = await send_whatsapp_text(request.phone, request.text)
        
        if send_result.get("status") != "success":
            error_msg = send_result.get("error", "Unknown error")
            logger.error(f"Failed to send WhatsApp message: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send WhatsApp message: {error_msg}"
            )
        
        message_id = send_result.get("message_id", "")
        logger.info(f"WhatsApp message sent successfully: {message_id}")
        
        # Step 2: Persist outbound message to database
        # Note: We use a generic user_id since this is a system-initiated notification
        # In production, you'd look up the user by phone first
        try:
            # Try to get user_id from phone (simplified for now)
            from app.models.user_model import get_user_by_phone
            user = await get_user_by_phone(db, request.phone)
            user_id = user.get("user_id", "system") if user else "system"
            
            # Create message document
            message_doc = create_message_doc(
                user_id=user_id,
                phone=request.phone,
                metadata={},
                role="bot",
                text=request.text,
                model=request.provider
            )
            
            # Save to database
            await save_message(db, message_doc)
            logger.info(f"Persisted outbound message: {message_doc['message_id']}")
        
        except Exception as e:
            # Log error but don't fail the request since message was sent
            logger.error(f"Failed to persist outbound message: {e}", exc_info=True)
        
        # Step 3: Return success response
        return SendNotificationResponse(
            status="success",
            message_id=message_id
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Log unexpected errors and return 500
        logger.error(f"Error sending notification to {request.phone}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
