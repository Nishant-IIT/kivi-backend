"""
JWT Handler Utilities

Purpose:
    Wrapper functions for JWT encoding and decoding operations.
    Provides a simplified interface around PyJWT library for token management.

Dependencies:
    - jwt (PyJWT): JWT encoding/decoding
    - datetime: Token expiration handling

Usage:
    from app.utils.jwt_handler import encode_jwt, decode_jwt
    
    # Encode a token
    token = encode_jwt({"user_id": "usr_123", "phone": "+919876543210"})
    
    # Decode a token
    payload = decode_jwt(token)
    print(payload["user_id"])
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.config.config import JWT_SECRET, JWT_EXPIRATION_HOURS


def encode_jwt(payload: Dict[str, Any], expires_in_hours: Optional[int] = None) -> str:
    """
    Encode a JWT token with the given payload.
    
    Args:
        payload: Dictionary containing token data (user_id, phone, etc.)
        expires_in_hours: Optional custom expiration time in hours.
                         Defaults to JWT_EXPIRATION_HOURS from config.
    
    Returns:
        Encoded JWT token string
        
    Example:
        token = encode_jwt({"user_id": "usr_123", "phone": "+919876543210"})
    """
    # Create a copy to avoid modifying the original payload
    token_payload = payload.copy()
    
    # Set expiration time
    expiration_hours = expires_in_hours if expires_in_hours is not None else JWT_EXPIRATION_HOURS
    expiration_time = datetime.utcnow() + timedelta(hours=expiration_hours)
    
    # Add standard JWT claims
    token_payload["exp"] = expiration_time
    token_payload["iat"] = datetime.utcnow()
    
    # Encode the token
    token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
    
    return token


def decode_jwt(token: str, verify: bool = True) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string to decode
        verify: Whether to verify the token signature and expiration.
               Defaults to True.
    
    Returns:
        Decoded payload dictionary
        
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
        
    Example:
        try:
            payload = decode_jwt(token)
            user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            print("Token expired")
        except jwt.InvalidTokenError:
            print("Invalid token")
    """
    if verify:
        # Decode with verification
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    else:
        # Decode without verification (useful for debugging)
        payload = jwt.decode(token, options={"verify_signature": False})
    
    return payload


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a JWT token without full verification.
    
    Args:
        token: JWT token string
        
    Returns:
        Expiration datetime or None if not present
        
    Example:
        exp_time = get_token_expiration(token)
        if exp_time and exp_time < datetime.utcnow():
            print("Token has expired")
    """
    try:
        payload = decode_jwt(token, verify=False)
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)
        return None
    except Exception:
        return None
