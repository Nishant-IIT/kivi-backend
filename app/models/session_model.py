"""
Session Data Model

Purpose:
    Defines session data structure for JWT refresh token management.
    Provides async functions for session CRUD operations supporting both
    mock data and MongoDB backends.

Dependencies:
    - pydantic: Data validation and serialization
    - app.db.mongodb: Database access layer

Usage:
    from app.models.session_model import Session, create_session, get_session
    
    # Create session with refresh token
    session = await create_session(
        db,
        user_id="usr_1234567890",
        refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    
    # Retrieve session by ID
    session = await get_session(db, "sess_1234567890_20250121...")

Reference:
    Requirements: 5.1, 5.2
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("kivi.db")


class Session(BaseModel):
    """
    Session data model for JWT refresh token management.
    
    Stores refresh tokens with expiration for secure authentication.
    Supports session validation and token refresh workflows.
    """
    session_id: str
    user_id: str
    refresh_token: str
    created_at: str
    expires_at: str


async def create_session(
    db: Any,
    user_id: str,
    refresh_token: str,
    expiration_days: int = 30
) -> Dict[str, Any]:
    """
    Store session with refresh token.
    
    Creates a new session record with automatic expiration. Generates
    session_id and timestamps automatically.
    
    Args:
        db: Database instance (MockDatabase or AsyncIOMotorDatabase)
        user_id: User identifier
        refresh_token: JWT refresh token string
        expiration_days: Number of days until session expires (default: 30)
    
    Returns:
        Created session document dict
    
    Raises:
        ValueError: If user_id or refresh_token is missing
        Exception: If database operation fails
    
    Example:
        session = await create_session(
            db,
            user_id="usr_1234567890",
            refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        )
        print(f"Session created: {session['session_id']}")
    """
    try:
        # Validate required fields
        if not user_id:
            raise ValueError("user_id is required for session creation")
        if not refresh_token:
            raise ValueError("refresh_token is required for session creation")
        
        logger.debug(f"Creating session for user {user_id}")
        
        # Generate session_id
        timestamp_str = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        session_id = f"sess_{user_id[-10:]}_{timestamp_str}"
        
        # Generate timestamps
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(days=expiration_days)
        
        # Create session document
        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "refresh_token": refresh_token,
            "created_at": created_at.isoformat() + "Z",
            "expires_at": expires_at.isoformat() + "Z"
        }
        
        # Insert session
        result = await db.sessions.insert_one(session_doc)
        
        logger.info(f"Created session {session_id} for user {user_id} "
                   f"(expires: {session_doc['expires_at']})")
        
        return session_doc
    
    except ValueError as e:
        logger.error(f"Validation error creating session: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating session for user {user_id}: {e}", exc_info=True)
        raise


async def get_session(db: Any, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve session by session ID.
    
    Fetches session document from database. Does not validate expiration -
    caller should check expires_at field.
    
    Args:
        db: Database instance (MockDatabase or AsyncIOMotorDatabase)
        session_id: Session identifier
    
    Returns:
        Session document dict or None if not found
    
    Example:
        session = await get_session(db, "sess_1234567890_20250121...")
        if session:
            # Check if expired
            expires_at = datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00'))
            if datetime.utcnow() > expires_at:
                print("Session expired")
            else:
                print(f"Valid session for user: {session['user_id']}")
        else:
            print("Session not found")
    """
    try:
        logger.debug(f"Getting session: {session_id}")
        
        session = await db.sessions.find_one({"session_id": session_id})
        
        if session:
            logger.info(f"Found session {session_id} for user {session.get('user_id', 'unknown')}")
        else:
            logger.debug(f"No session found with ID: {session_id}")
        
        return session
    
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}", exc_info=True)
        return None
