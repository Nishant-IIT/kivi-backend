"""
MongoDB Connection Layer

Purpose:
    Provides async MongoDB connection management using Motor driver.
    Implements lifecycle management (connect/close) and database access.

Dependencies:
    - motor: Async MongoDB driver
    - app.config.config: Configuration constants

Usage:
    # In FastAPI startup
    await connect_db()
    
    # In route handlers
    db = get_db()
    users = await db.users.find_one({"phone": phone})
    
    # In FastAPI shutdown
    await close_db()

Reference:
    Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 20.8, 20.9
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config.config import MONGO_URI
import logging

logger = logging.getLogger("kivi.db")

# Global MongoDB client
client: Optional[AsyncIOMotorClient] = None


async def connect_db() -> None:
    """
    Initialize MongoDB connection.
    
    Creates async Motor client and tests connection with ping command.
    
    Raises:
        Exception: If connection fails
    """
    global client
    
    try:
        logger.info(f"Connecting to MongoDB at {MONGO_URI}")
        client = AsyncIOMotorClient(MONGO_URI)
        
        # Test connection
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}", exc_info=True)
        raise


async def close_db() -> None:
    """
    Close MongoDB connection.
    
    Gracefully closes the Motor client connection.
    Safe to call even if not connected.
    """
    global client
    
    if client:
        logger.info("Closing MongoDB connection")
        client.close()
        client = None
    else:
        logger.debug("No MongoDB connection to close")


def get_db() -> AsyncIOMotorDatabase:
    """
    Get database instance.
    
    Returns:
        AsyncIOMotorDatabase: Database instance
    
    Raises:
        RuntimeError: If database not connected
    """
    if client is None:
        logger.error("MongoDB client not initialized - call connect_db() first")
        raise RuntimeError("Database not connected. Call connect_db() first.")
    
    return client.kivi_db
