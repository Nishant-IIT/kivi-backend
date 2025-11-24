"""
WhatsApp Service Module

Purpose:
    Handles incoming WhatsApp webhooks from Meta Cloud API and sends outbound messages.
    Processes user messages, generates AI responses, and manages conversation flow.
    Integrates with user profiles, message logging, and AI chat services.

Dependencies:
    - httpx: Async HTTP client for Meta Graph API calls
    - app.models.user_model: User profile operations
    - app.models.message_log_model: Message persistence
    - app.services.ai_chat: AI response generation
    - app.config.config: WhatsApp API credentials
    - app.config.logging_config: Logging utilities

Usage:
    from app.services.whatsapp_service import handle_incoming_webhook, send_whatsapp_text
    
    # Process incoming webhook
    await handle_incoming_webhook(db, webhook_payload)
    
    # Send outbound message
    result = await send_whatsapp_text("+919876543210", "Hello from KIVI!")

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.2, 8.3, 8.4, 8.5
"""

import httpx
from typing import Dict, Any, Optional
from app.models.user_model import get_user_by_phone, create_empty_user, upsert_user
from app.models.message_log_model import create_message_doc, save_message
from app.services.ai_chat import chat_with_model
from app.config.config import WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN
from app.config.logging_config import webhook_logger


# Meta WhatsApp Cloud API endpoint
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"


async def handle_incoming_webhook(db: Any, payload: Dict[str, Any]) -> None:
    """
    Process incoming WhatsApp message and respond with AI-generated reply.
    
    Workflow:
    1. Validate webhook signature/token
    2. Extract phone, user_id, message from Meta webhook payload
    3. Get user profile to build metadata context
    4. Persist user message using message_log_model
    5. Call chat_with_model() to get AI response
    6. Persist bot message
    7. Send reply via send_whatsapp_text()
    
    Args:
        db: Database instance (MockDatabase or AsyncIOMotorDatabase)
        payload: Meta webhook payload containing message data
    
    Raises:
        ValueError: If webhook validation fails or required fields missing
        Exception: If processing fails
    
    Example payload structure:
        {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "919876543210",
                            "id": "wamid.xxx",
                            "text": {"body": "How much did I spend on food?"},
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }
    """
    try:
        webhook_logger.info("Received WhatsApp webhook")
        webhook_logger.debug(f"Webhook payload: {payload}")
        
        # Validate webhook structure
        if "object" not in payload or payload["object"] != "whatsapp_business_account":
            webhook_logger.warning(f"Invalid webhook object type: {payload.get('object')}")
            raise ValueError("Invalid webhook object type")
        
        # Extract message data from nested structure
        if "entry" not in payload or not payload["entry"]:
            webhook_logger.warning("No entry field in webhook payload")
            raise ValueError("No entry field in webhook payload")
        
        entry = payload["entry"][0]
        
        if "changes" not in entry or not entry["changes"]:
            webhook_logger.warning("No changes field in webhook entry")
            raise ValueError("No changes field in webhook entry")
        
        change = entry["changes"][0]
        value = change.get("value", {})
        
        # Check if this is a message event
        if "messages" not in value or not value["messages"]:
            webhook_logger.debug("Webhook does not contain messages (might be status update)")
            return
        
        message_data = value["messages"][0]
        
        # Extract phone number (add + prefix if not present)
        phone = message_data.get("from", "")
        if not phone.startswith("+"):
            phone = f"+{phone}"
        
        # Extract message text
        message_text = message_data.get("text", {}).get("body", "")
        
        if not phone or not message_text:
            webhook_logger.warning(f"Missing phone or message text: phone={phone}, text={message_text}")
            raise ValueError("Missing phone number or message text")
        
        webhook_logger.info(f"Processing message from {phone}: {message_text[:50]}...")
        
        # Get or create user profile
        user = await get_user_by_phone(db, phone)
        
        if not user:
            webhook_logger.info(f"New user detected: {phone}. Creating profile.")
            new_user = create_empty_user(phone)
            user = await upsert_user(db, new_user)
            webhook_logger.info(f"Created user profile for {phone}")
        
        user_id = user.get("user_id", "")
        
        # Build metadata context for AI
        metadata = _build_user_metadata(user)
        
        # Persist user message
        user_message_doc = create_message_doc(
            user_id=user_id,
            phone=phone,
            metadata=metadata,
            role="user",
            text=message_text,
            model=None
        )
        
        await save_message(db, user_message_doc)
        webhook_logger.debug(f"Saved user message: {user_message_doc['message_id']}")
        
        # Get AI response
        webhook_logger.info(f"Calling AI chat service for user {user_id}")
        ai_response = await chat_with_model(
            metadata=metadata,
            message=message_text,
            provider="openai"  # Default to OpenAI
        )
        
        reply_text = ai_response.get("reply", "")
        provider = ai_response.get("provider", "openai")
        
        webhook_logger.info(f"Received AI response ({len(reply_text)} chars) from {provider}")
        
        # Persist bot message
        bot_message_doc = create_message_doc(
            user_id=user_id,
            phone=phone,
            metadata=metadata,
            role="bot",
            text=reply_text,
            model=provider
        )
        
        await save_message(db, bot_message_doc)
        webhook_logger.debug(f"Saved bot message: {bot_message_doc['message_id']}")
        
        # Send reply via WhatsApp
        send_result = await send_whatsapp_text(phone, reply_text)
        
        if send_result.get("status") == "success":
            webhook_logger.info(f"Successfully sent WhatsApp reply to {phone}")
        else:
            webhook_logger.error(f"Failed to send WhatsApp reply: {send_result.get('error')}")
    
    except ValueError as e:
        webhook_logger.error(f"Validation error processing webhook: {e}")
        raise
    
    except Exception as e:
        webhook_logger.error(f"Error processing WhatsApp webhook: {e}", exc_info=True)
        raise


async def send_whatsapp_text(phone: str, text: str) -> Dict[str, Any]:
    """
    Send WhatsApp message via Meta Cloud API.
    
    Posts to Meta Graph API using WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID.
    Handles API errors and returns status.
    
    Args:
        phone: Recipient phone number (e.g., "+919876543210" or "919876543210")
        text: Message text to send
    
    Returns:
        dict: Result dictionary containing:
            - status (str): "success" or "error"
            - message_id (str): WhatsApp message ID if successful
            - error (str): Error message if failed
    
    Example:
        result = await send_whatsapp_text("+919876543210", "Hello from KIVI!")
        if result["status"] == "success":
            print(f"Message sent: {result['message_id']}")
    """
    try:
        # Remove + prefix if present (Meta API expects without +)
        phone_clean = phone.lstrip("+")
        
        webhook_logger.info(f"Sending WhatsApp message to {phone_clean}")
        webhook_logger.debug(f"Message text: {text[:100]}...")
        
        # Check if we have valid credentials
        if "placeholder" in WHATSAPP_TOKEN.lower() or "placeholder" in WHATSAPP_PHONE_NUMBER_ID.lower():
            webhook_logger.warning("WhatsApp credentials not configured. Returning mock success.")
            return {
                "status": "success",
                "message_id": "mock_msg_id_12345",
                "note": "Mock response - WhatsApp credentials not configured"
            }
        
        # Build Meta API request payload
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_clean,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }
        
        # Build headers with authentication
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Make API request with retry logic
        async with httpx.AsyncClient(timeout=30.0) as client:
            webhook_logger.debug(f"POST {WHATSAPP_API_URL}")
            
            response = await client.post(
                WHATSAPP_API_URL,
                json=payload,
                headers=headers
            )
            
            webhook_logger.debug(f"WhatsApp API response status: {response.status_code}")
            
            # Check response status
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get("messages", [{}])[0].get("id", "")
                
                webhook_logger.info(f"WhatsApp message sent successfully: {message_id}")
                
                return {
                    "status": "success",
                    "message_id": message_id
                }
            else:
                error_data = response.json() if response.text else {}
                error_message = error_data.get("error", {}).get("message", response.text)
                
                webhook_logger.error(
                    f"WhatsApp API error (status {response.status_code}): {error_message}"
                )
                
                return {
                    "status": "error",
                    "error": f"API error {response.status_code}: {error_message}"
                }
    
    except httpx.TimeoutException as e:
        webhook_logger.error(f"WhatsApp API timeout: {e}")
        return {
            "status": "error",
            "error": f"Request timeout: {str(e)}"
        }
    
    except httpx.RequestError as e:
        webhook_logger.error(f"WhatsApp API request error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": f"Request error: {str(e)}"
        }
    
    except Exception as e:
        webhook_logger.error(f"Unexpected error sending WhatsApp message: {e}", exc_info=True)
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}"
        }


def _build_user_metadata(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build metadata context from user profile for AI prompts.
    
    Extracts relevant user information to provide context for AI responses.
    
    Args:
        user: User profile document
    
    Returns:
        Metadata dictionary with user context
    """
    metadata = {
        "name": user.get("name", "User"),
        "job": user.get("job", ""),
        "gig_platforms": user.get("gig_platforms", []),
        "transaction_summary": user.get("financial_summary", {}),
        "goals": user.get("goals", []),
        "budgets": user.get("budgets", [])
    }
    
    return metadata


# Example usage (commented out)
"""
import asyncio
from app.db.mongodb import get_db

async def example_usage():
    db = get_db()
    
    # Example webhook payload from Meta
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456789",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "919876543210",
                        "phone_number_id": "123456789"
                    },
                    "contacts": [{
                        "profile": {"name": "Rahul"},
                        "wa_id": "919876543210"
                    }],
                    "messages": [{
                        "from": "919876543210",
                        "id": "wamid.HBgNOTE5ODc2NTQzMjEwFQIAERgSMDhBRjE2QjdGNzY4QzQ5OTJBAA==",
                        "timestamp": "1234567890",
                        "text": {
                            "body": "How much did I spend on food this month?"
                        },
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    # Process webhook
    await handle_incoming_webhook(db, webhook_payload)
    
    # Send direct message
    result = await send_whatsapp_text("+919876543210", "Your food spending this month is ₹3,200")
    print(f"Send result: {result}")

if __name__ == "__main__":
    asyncio.run(example_usage())
"""
