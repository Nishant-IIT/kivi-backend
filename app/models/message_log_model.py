"""
Message Log Data Model

Purpose:
    Defines message log data structure for chat conversation tracking.
    Provides functions for creating, saving, and retrieving message logs
    supporting both mock data and MongoDB backends.

Dependencies:
    - pydantic: Data validation and serialization
    - app.db.mongodb: Database access layer

Usage:
    from app.models.message_log_model import MessageLog, create_message_doc, save_message, get_conversation_history
    
    # Create message document
    msg_doc = create_message_doc(
        user_id="usr_1234567890",
        phone="+919876543210",
        metadata={"name": "Rahul", "balance": 12000},
        role="user",
        text="How much did I spend on food?",
        model=None
    )
    
    # Save message to database
    await save_message(db, msg_doc)
    
    # Get conversation history
    history = await get_conversation_history(db, "usr_1234567890", limit=50)

Reference:
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 20.3
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger("kivi.db")


class MessageLog(BaseModel):
    """
    Message log data model for chat conversation tracking.
    
    Stores both user and bot messages with metadata context for AI interactions.
    Supports conversation history retrieval and audit logging.
    """
    message_id: str
    user_id: str
    phone: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    role: str  # user or bot
    text: str
    provider: Optional[str] = None
    timestamp: str


def create_message_doc(
    user_id: str,
    phone: str,
    metadata: Dict[str, Any],
    role: str,
    text: str,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create message document for insertion.
    
    Generates message_id and timestamp automatically. Validates role field.
    
    Args:
        user_id: User identifier
        phone: User phone number
        metadata: User context dictionary (name, job, goals, transaction_summary)
        role: Message role - "user" or "bot"
        text: Message text content
        model: AI model/provider name (optional, for bot messages)
    
    Returns:
        Message document dict ready for database insertion
    
    Raises:
        ValueError: If role is not "user" or "bot"
    
    Example:
        # User message
        user_msg = create_message_doc(
            user_id="usr_1234567890",
            phone="+919876543210",
            metadata={"name": "Rahul", "balance": 12000},
            role="user",
            text="How much did I spend on food this month?"
        )
        
        # Bot message
        bot_msg = create_message_doc(
            user_id="usr_1234567890",
            phone="+919876543210",
            metadata={"name": "Rahul", "balance": 12000},
            role="bot",
            text="You spent ₹3,200 on food this month.",
            model="openai"
        )
    """
    # Validate role
    if role not in ["user", "bot"]:
        raise ValueError(f"Invalid role: {role}. Must be 'user' or 'bot'")
    
    logger.debug(f"Creating message document for user {user_id}, role={role}")
    
    # Generate message_id
    timestamp_str = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    message_id = f"msg_{user_id[-10:]}_{timestamp_str}"
    
    # Generate timestamp
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    message_doc = {
        "message_id": message_id,
        "user_id": user_id,
        "phone": phone,
        "metadata": metadata if metadata else {},
        "role": role,
        "text": text,
        "provider": model,
        "timestamp": timestamp
    }
    
    logger.debug(f"Created message document {message_id} with {len(text)} characters")
    
    return message_doc


async def save_message(db: Any, message_doc: Dict[str, Any]) -> None:
    """
    Persist message to database.
    
    Inserts message document into message_logs collection with error handling.
    Supports both MockDatabase and MongoDB backends.
    
    Args:
        db: Database instance (MockDatabase or AsyncIOMotorDatabase)
        message_doc: Message document dict from create_message_doc()
    
    Raises:
        ValueError: If required fields are missing
        Exception: If database operation fails
    
    Example:
        msg_doc = create_message_doc(
            user_id="usr_1234567890",
            phone="+919876543210",
            metadata={},
            role="user",
            text="Hello"
        )
        await save_message(db, msg_doc)
    """
    try:
        # Validate required fields
        required_fields = ["message_id", "user_id", "phone", "role", "text", "timestamp"]
        missing_fields = [field for field in required_fields if field not in message_doc]
        
        if missing_fields:
            raise ValueError(f"Missing required fields in message document: {', '.join(missing_fields)}")
        
        logger.debug(f"Saving message {message_doc['message_id']} for user {message_doc['user_id']}")
        
        # Insert message
        result = await db.message_logs.insert_one(message_doc)
        
        logger.info(f"Saved message {message_doc['message_id']} "
                   f"(role={message_doc['role']}, user={message_doc['user_id']})")
    
    except ValueError as e:
        logger.error(f"Validation error saving message: {e}")
        raise
    except Exception as e:
        logger.error(f"Error saving message {message_doc.get('message_id', 'unknown')}: {e}", 
                    exc_info=True)
        raise


async def get_conversation_history(
    db: Any,
    user_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retrieve recent messages for user.
    
    Returns conversation history sorted by timestamp (oldest first) for
    context building in AI prompts. Uses compound index on user_id + timestamp.
    
    Args:
        db: Database instance (MockDatabase or AsyncIOMotorDatabase)
        user_id: User identifier
        limit: Maximum number of messages to retrieve (default: 50)
    
    Returns:
        List of message documents sorted by timestamp (oldest first)
    
    Example:
        # Get last 50 messages
        history = await get_conversation_history(db, "usr_1234567890")
        
        # Get last 10 messages
        recent = await get_conversation_history(db, "usr_1234567890", limit=10)
        
        # Build context for AI
        context = "\n".join([
            f"{msg['role']}: {msg['text']}"
            for msg in history
        ])
    """
    try:
        logger.debug(f"Getting conversation history for user {user_id} (limit={limit})")
        
        # Query messages for user
        query = {"user_id": user_id}
        messages = await db.message_logs.find(query)
        
        # Sort by timestamp (oldest first for conversation flow)
        messages_sorted = sorted(
            messages,
            key=lambda x: x.get("timestamp", "")
        )
        
        # Apply limit (take most recent N messages)
        if len(messages_sorted) > limit:
            messages_sorted = messages_sorted[-limit:]
        
        logger.info(f"Retrieved {len(messages_sorted)} messages for user {user_id}")
        
        return messages_sorted
    
    except Exception as e:
        logger.error(f"Error getting conversation history for user {user_id}: {e}", 
                    exc_info=True)
        return []
