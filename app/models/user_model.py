"""
User Data Model

Purpose:
    Defines user profile data structure with gig worker specific fields.
    Provides async functions for user CRUD operations supporting both
    mock data and MongoDB backends.

Dependencies:
    - pydantic: Data validation and serialization
    - app.db.mongodb: Database access layer

Usage:
    from app.models.user_model import UserProfile, get_user_by_phone, upsert_user
    
    # Get user by phone
    user = await get_user_by_phone(db, "+919876543210")
    
    # Create or update user
    updated_user = await upsert_user(db, user_dict)
    
    # Create sample user for onboarding
    sample_user = create_sample_user("+919876543210")

Reference:
    Requirements: 6.3, 6.4, 6.5, 19.1, 19.2, 19.3, 20.1
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger("kivi.db")


def serialize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB document to JSON-serializable dict.
    
    Converts ObjectId to string and handles nested documents.
    
    Args:
        doc: MongoDB document
    
    Returns:
        JSON-serializable dictionary
    """
    if doc is None:
        return None
    
    # Convert _id ObjectId to string
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    
    return doc


class FinancialSummary(BaseModel):
    """Financial summary for gig worker profile."""
    current_balance: float = 0.0
    avg_monthly_income: float = 0.0
    monthly_expenses: float = 0.0
    income_volatility: str = "medium"  # low, medium, high
    last_30_days_income: float = 0.0
    income_sources: Dict[str, float] = Field(default_factory=dict)


class Budget(BaseModel):
    """Budget configuration for spending category."""
    category: str
    monthly_limit: float
    current_spent: float = 0.0
    note: Optional[str] = None


class Goal(BaseModel):
    """Financial goal with target and progress."""
    goal_id: str
    name: str
    target_amount: float
    current_amount: float = 0.0
    deadline: Optional[str] = None
    priority: str = "medium"  # low, medium, high


class NotificationPreferences(BaseModel):
    """User notification preferences."""
    whatsapp_enabled: bool = True
    budget_alerts: bool = True
    weekly_summary: bool = True
    income_tracking: bool = True
    low_balance_threshold: float = 5000.0


class UserProfile(BaseModel):
    """
    User profile data model with gig worker specific fields.
    
    Includes financial summary with income volatility tracking,
    multiple income sources, budgets, goals, and notification preferences.
    """
    user_id: str
    phone: str
    name: str
    email: Optional[str] = None
    job: Optional[str] = None
    city: Optional[str] = None
    gig_platforms: List[str] = Field(default_factory=list)
    financial_summary: FinancialSummary = Field(default_factory=FinancialSummary)
    budgets: List[Budget] = Field(default_factory=list)
    goals: List[Goal] = Field(default_factory=list)
    notification_preferences: NotificationPreferences = Field(default_factory=NotificationPreferences)
    created_at: str
    updated_at: str


async def get_user_by_phone(db: Any, phone: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve user by phone number.
    
    Supports both MockDatabase and MongoDB backends.
    
    Args:
        db: Database instance (MockDatabase or AsyncIOMotorDatabase)
        phone: User phone number (e.g., "+919876543210")
    
    Returns:
        User document dict or None if not found
    
    Example:
        user = await get_user_by_phone(db, "+919876543210")
        if user:
            print(f"Found user: {user['name']}")
    """
    try:
        logger.debug(f"Getting user by phone: {phone}")
        user = await db.users.find_one({"phone": phone})
        
        if user:
            # Convert MongoDB ObjectId to string for JSON serialization
            user = serialize_mongo_doc(user)
            logger.info(f"Found user: {user.get('user_id', 'unknown')}")
        else:
            logger.debug(f"No user found with phone: {phone}")
        
        return user
    
    except Exception as e:
        logger.error(f"Error getting user by phone {phone}: {e}", exc_info=True)
        return None


async def upsert_user(db: Any, user_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create or update user profile.
    
    Uses phone number as unique identifier. Updates timestamp on modification.
    Supports both MockDatabase and MongoDB backends.
    
    Args:
        db: Database instance (MockDatabase or AsyncIOMotorDatabase)
        user_dict: User data dictionary
    
    Returns:
        Updated user document dict
    
    Raises:
        ValueError: If phone number is missing
        Exception: If database operation fails
    
    Example:
        user_data = {
            "phone": "+919876543210",
            "name": "Rahul Sharma",
            "job": "Delivery Partner"
        }
        user = await upsert_user(db, user_data)
    """
    try:
        if "phone" not in user_dict:
            raise ValueError("Phone number is required for user upsert")
        
        phone = user_dict["phone"]
        logger.debug(f"Upserting user with phone: {phone}")
        
        # Update timestamp
        user_dict["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # If no created_at, add it
        if "created_at" not in user_dict:
            user_dict["created_at"] = user_dict["updated_at"]
        
        # Perform upsert
        result = await db.users.update_one(
            {"phone": phone},
            {"$set": user_dict},
            upsert=True
        )
        
        if result.matched_count > 0:
            logger.info(f"Updated existing user: {phone}")
        else:
            logger.info(f"Created new user: {phone}")
        
        # Return the updated user
        user = await get_user_by_phone(db, phone)
        return user
    
    except Exception as e:
        logger.error(f"Error upserting user: {e}", exc_info=True)
        raise


def create_empty_user(phone: str, name: str = "User") -> Dict[str, Any]:
    """
    Create minimal user profile for new users.
    
    Args:
        phone: User phone number
        name: User's name (optional)
    
    Returns:
        User document dict with minimal data
    """
    logger.info(f"Creating new user profile for phone: {phone}")
    
    # Generate user_id from phone (remove + and take last 10 digits)
    user_id = f"usr_{phone.replace('+', '').replace('-', '')[-10:]}"
    
    now = datetime.utcnow().isoformat() + "Z"
    
    user = {
        "user_id": user_id,
        "phone": phone,
        "name": name,
        "email": None,
        "job": None,
        "city": None,
        "gig_platforms": [],
        "financial_summary": {
            "current_balance": 0.0,
            "avg_monthly_income": 0.0,
            "monthly_expenses": 0.0,
            "income_volatility": "medium",
            "last_30_days_income": 0.0,
            "income_sources": {}
        },
        "budgets": [],
        "goals": [],
        "notification_preferences": {
            "whatsapp_enabled": True,
            "budget_alerts": True,
            "weekly_summary": True,
            "income_tracking": True,
            "low_balance_threshold": 5000.0
        },
        "created_at": now,
        "updated_at": now
    }
    
    return user
