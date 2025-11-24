"""
Security and Authentication Module

Purpose:
    Provides JWT token creation, verification, and FastAPI authentication
    dependencies for protected endpoints. Handles user authentication
    without OTP-based flows.

Dependencies:
    - jwt (PyJWT): JWT token operations
    - fastapi: Security dependencies
    - app.utils.jwt_handler: JWT encoding/decoding wrappers
    - app.core.exceptions: Custom exception classes

Usage:
    from app.core.security import create_token, verify_token, get_current_user
    
    # Create a token
    token = create_token("usr_123", "+919876543210")
    
    # Verify a token
    payload = verify_token(token)
    
    # Use as FastAPI dependency
    @app.get("/protected")
    async def protected_route(current_user: dict = Depends(get_current_user)):
        return {"user": current_user}
"""

import jwt
from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.jwt_handler import encode_jwt, decode_jwt
from app.core.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    InvalidTokenError
)


# FastAPI security scheme for Bearer token
security_scheme = HTTPBearer()


def create_token(user_id: str, phone: str) -> str:
    """
    Generate a JWT token for authenticated user.
    
    Args:
        user_id: Unique user identifier
        phone: User's phone number
        
    Returns:
        JWT token string
        
    Example:
        token = create_token("usr_123", "+919876543210")
        # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    payload = {
        "user_id": user_id,
        "phone": phone
    }
    
    token = encode_jwt(payload)
    return token


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token with expiration checking.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded payload dictionary containing user_id, phone, exp, iat
        
    Raises:
        TokenExpiredError: If token has expired
        InvalidTokenError: If token is invalid or malformed
        
    Example:
        try:
            payload = verify_token(token)
            user_id = payload["user_id"]
            phone = payload["phone"]
        except TokenExpiredError:
            print("Token expired, please login again")
        except InvalidTokenError:
            print("Invalid token")
    """
    try:
        # Decode and verify the token
        payload = decode_jwt(token, verify=True)
        return payload
        
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired, please login again")
        
    except jwt.InvalidTokenError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")
        
    except Exception as e:
        raise InvalidTokenError(f"Token verification failed: {str(e)}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> Dict[str, Any]:
    """
    FastAPI dependency for protected endpoints.
    Extracts and verifies JWT token from Authorization header.
    
    Args:
        credentials: HTTP Bearer token credentials from request header
        
    Returns:
        Dictionary containing user information (user_id, phone)
        
    Raises:
        HTTPException: 401 if token is missing, invalid, or expired
        
    Usage:
        @app.get("/users/me")
        async def get_profile(current_user: dict = Depends(get_current_user)):
            return {"user_id": current_user["user_id"]}
    """
    token = credentials.credentials
    
    try:
        # Verify the token
        payload = verify_token(token)
        
        # Extract user information
        user_info = {
            "user_id": payload.get("user_id"),
            "phone": payload.get("phone")
        }
        
        # Validate required fields are present
        if not user_info["user_id"] or not user_info["phone"]:
            raise InvalidTokenError("Token missing required user information")
        
        return user_info
        
    except TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )



