"""
MongoDB Connection Layer

Purpose:
    Provides async MongoDB connection management using Motor driver.
    Supports both real MongoDB and in-memory mock data for development.
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

from typing import Optional, Any, Dict, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config.config import MONGO_URI, USE_MOCK_DATA
import logging

logger = logging.getLogger("kivi.db")

# Global MongoDB client
client: Optional[AsyncIOMotorClient] = None

# Global mock database instance (persists across requests)
mock_db: Optional["MockDatabase"] = None


async def connect_db() -> None:
    """
    Initialize MongoDB connection.
    
    Creates async Motor client and tests connection with ping command.
    Only connects if USE_MOCK_DATA is False.
    
    Raises:
        Exception: If connection fails
    """
    global client
    
    if USE_MOCK_DATA:
        logger.info("Using mock data - skipping MongoDB connection")
        return
    
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


def get_db() -> Any:
    """
    Get database instance.
    
    Returns MockDatabase when USE_MOCK_DATA=true, otherwise returns
    real MongoDB database instance.
    
    Returns:
        MockDatabase or AsyncIOMotorDatabase: Database instance
    """
    global mock_db
    
    if USE_MOCK_DATA:
        # Use singleton mock database to persist data across requests
        if mock_db is None:
            logger.info("Creating singleton MockDatabase instance")
            mock_db = MockDatabase()
        logger.debug("Returning singleton MockDatabase instance")
        return mock_db
    
    if client is None:
        logger.error("MongoDB client not initialized - call connect_db() first")
        raise RuntimeError("Database not connected. Call connect_db() first.")
    
    return client.kivi_db


class MockCollection:
    """
    Mock MongoDB collection with in-memory storage.
    
    Implements collection-like interface matching MongoDB API for common operations.
    Supports find_one, find, insert_one, update_one, delete_one operations.
    """
    
    def __init__(self, name: str, data: List[Dict[str, Any]]):
        """
        Initialize mock collection.
        
        Args:
            name: Collection name
            data: Reference to shared data list
        """
        self.name = name
        self.data = data
    
    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find single document matching filter.
        
        Args:
            filter_dict: Query filter (e.g., {"phone": "+919876543210"})
        
        Returns:
            Matching document or None
        """
        logger.debug(f"MockCollection.{self.name}.find_one({filter_dict})")
        
        for doc in self.data:
            if self._matches_filter(doc, filter_dict):
                return doc
        return None
    
    async def find(self, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Find all documents matching filter.
        
        Args:
            filter_dict: Query filter (optional, returns all if None)
        
        Returns:
            List of matching documents
        """
        if filter_dict is None:
            filter_dict = {}
        
        logger.debug(f"MockCollection.{self.name}.find({filter_dict})")
        
        results = []
        for doc in self.data:
            if self._matches_filter(doc, filter_dict):
                results.append(doc)
        return results
    
    async def insert_one(self, document: Dict[str, Any]) -> Any:
        """
        Insert single document.
        
        Args:
            document: Document to insert
        
        Returns:
            Mock insert result with inserted_id
        """
        logger.debug(f"MockCollection.{self.name}.insert_one({document.get('_id', 'no-id')})")
        
        self.data.append(document)
        
        # Return mock result
        class MockInsertResult:
            def __init__(self, doc_id):
                self.inserted_id = doc_id
        
        return MockInsertResult(document.get("_id", len(self.data) - 1))
    
    async def update_one(
        self, 
        filter_dict: Dict[str, Any], 
        update: Dict[str, Any],
        upsert: bool = False
    ) -> Any:
        """
        Update single document matching filter.
        
        Args:
            filter_dict: Query filter
            update: Update operations (e.g., {"$set": {...}})
            upsert: Insert if not found
        
        Returns:
            Mock update result
        """
        logger.debug(f"MockCollection.{self.name}.update_one({filter_dict}, upsert={upsert})")
        
        # Find matching document
        for i, doc in enumerate(self.data):
            if self._matches_filter(doc, filter_dict):
                # Apply update
                if "$set" in update:
                    doc.update(update["$set"])
                
                class MockUpdateResult:
                    def __init__(self, matched, modified):
                        self.matched_count = matched
                        self.modified_count = modified
                
                return MockUpdateResult(1, 1)
        
        # Handle upsert
        if upsert:
            new_doc = filter_dict.copy()
            if "$set" in update:
                new_doc.update(update["$set"])
            self.data.append(new_doc)
            
            class MockUpdateResult:
                def __init__(self, matched, modified, upserted_id):
                    self.matched_count = matched
                    self.modified_count = modified
                    self.upserted_id = upserted_id
            
            return MockUpdateResult(0, 0, new_doc.get("_id", len(self.data) - 1))
        
        class MockUpdateResult:
            def __init__(self, matched, modified):
                self.matched_count = matched
                self.modified_count = modified
        
        return MockUpdateResult(0, 0)
    
    async def delete_one(self, filter_dict: Dict[str, Any]) -> Any:
        """
        Delete single document matching filter.
        
        Args:
            filter_dict: Query filter
        
        Returns:
            Mock delete result
        """
        logger.debug(f"MockCollection.{self.name}.delete_one({filter_dict})")
        
        for i, doc in enumerate(self.data):
            if self._matches_filter(doc, filter_dict):
                self.data.pop(i)
                
                class MockDeleteResult:
                    def __init__(self, deleted):
                        self.deleted_count = deleted
                
                return MockDeleteResult(1)
        
        class MockDeleteResult:
            def __init__(self, deleted):
                self.deleted_count = deleted
        
        return MockDeleteResult(0)
    
    def _matches_filter(self, doc: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """
        Check if document matches filter.
        
        Supports exact matches, nested keys, and MongoDB query operators
        ($gte, $lte, $gt, $lt, $eq, $ne).
        
        Args:
            doc: Document to check
            filter_dict: Filter criteria
        
        Returns:
            True if document matches filter
        """
        for key, value in filter_dict.items():
            if key not in doc:
                return False
            
            # Handle nested keys (e.g., "metadata.name")
            if "." in key:
                parts = key.split(".")
                current = doc
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return False
                doc_value = current
            else:
                doc_value = doc[key]
            
            # Handle MongoDB query operators
            if isinstance(value, dict):
                for operator, operand in value.items():
                    if operator == "$gte":
                        if not (doc_value >= operand):
                            return False
                    elif operator == "$lte":
                        if not (doc_value <= operand):
                            return False
                    elif operator == "$gt":
                        if not (doc_value > operand):
                            return False
                    elif operator == "$lt":
                        if not (doc_value < operand):
                            return False
                    elif operator == "$eq":
                        if not (doc_value == operand):
                            return False
                    elif operator == "$ne":
                        if not (doc_value != operand):
                            return False
                    else:
                        # Unknown operator, treat as exact match
                        if doc_value != value:
                            return False
            else:
                # Exact match
                if doc_value != value:
                    return False
        
        return True


class MockDatabase:
    """
    Mock MongoDB database with in-memory collections.
    
    Provides collection-like interface for development without MongoDB.
    Collections: users, transactions, message_logs, notifications, user_rules, sessions
    """
    
    def __init__(self):
        """Initialize mock database with empty collections."""
        logger.debug("Initializing MockDatabase")
        
        # In-memory data storage
        self._users_data: List[Dict[str, Any]] = []
        self._transactions_data: List[Dict[str, Any]] = []
        self._message_logs_data: List[Dict[str, Any]] = []
        self._notifications_data: List[Dict[str, Any]] = []
        self._user_rules_data: List[Dict[str, Any]] = []
        self._sessions_data: List[Dict[str, Any]] = []
        
        # Collection instances
        self.users = MockCollection("users", self._users_data)
        self.transactions = MockCollection("transactions", self._transactions_data)
        self.message_logs = MockCollection("message_logs", self._message_logs_data)
        self.notifications = MockCollection("notifications", self._notifications_data)
        self.user_rules = MockCollection("user_rules", self._user_rules_data)
        self.sessions = MockCollection("sessions", self._sessions_data)
        
        logger.info("MockDatabase initialized with 6 collections")
    
    def __getattr__(self, name: str) -> MockCollection:
        """
        Dynamic collection access.
        
        Allows accessing collections as attributes (e.g., db.users).
        Creates new empty collection if not exists.
        
        Args:
            name: Collection name
        
        Returns:
            MockCollection instance
        """
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        # Create new collection dynamically
        logger.debug(f"Creating dynamic collection: {name}")
        new_data: List[Dict[str, Any]] = []
        collection = MockCollection(name, new_data)
        
        # Store in __dict__ to avoid recursion
        self.__dict__[f"_{name}_data"] = new_data
        self.__dict__[name] = collection
        
        return collection
