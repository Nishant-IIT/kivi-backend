"""
Transaction Data Model

Purpose:
    Defines transaction data structure for financial tracking.
    Provides async functions for transaction CRUD operations supporting both
    mock data and MongoDB backends with efficient querying.

Dependencies:
    - pydantic: Data validation and serialization
    - app.db.mongodb: Database access layer

Usage:
    from app.models.transaction_model import Transaction, get_transactions, create_transaction
    
    # Create transaction
    txn = {
        "user_id": "usr_1234567890",
        "amount": 450.0,
        "vendor": "Swiggy",
        "category": "food",
        "transaction_type": "debit"
    }
    created = await create_transaction(db, txn)
    
    # Query transactions
    transactions = await get_transactions(
        db, 
        user_id="usr_1234567890",
        start_date="2025-01-01T00:00:00Z",
        end_date="2025-01-31T23:59:59Z",
        category="food"
    )

Reference:
    Requirements: 7.5, 7.6, 20.2, 20.7
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger("kivi.db")


class Transaction(BaseModel):
    """
    Transaction data model for financial tracking.
    
    Supports transactions from multiple sources (SMS, Account Aggregator, manual entry)
    with categorization and metadata for analysis.
    """
    transaction_id: str
    user_id: str
    amount: float
    vendor: str
    category: str
    transaction_type: str  # debit or credit
    timestamp: str
    source: str  # sms, aa, manual
    raw_sms_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


async def get_transactions(
    db: Any,
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query transactions with filters.
    
    Supports filtering by date range and category. Uses compound index on
    user_id + timestamp for efficient queries.
    
    Args:
        db: Database instance (MockDatabase or AsyncIOMotorDatabase)
        user_id: User identifier
        start_date: Start date in ISO 8601 format (optional)
        end_date: End date in ISO 8601 format (optional)
        category: Transaction category filter (optional)
    
    Returns:
        List of transaction documents sorted by timestamp (newest first)
    
    Example:
        # Get all transactions for user
        txns = await get_transactions(db, "usr_1234567890")
        
        # Get food transactions for January 2025
        txns = await get_transactions(
            db,
            "usr_1234567890",
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-01-31T23:59:59Z",
            category="food"
        )
    """
    try:
        logger.debug(f"Getting transactions for user {user_id} "
                    f"(start={start_date}, end={end_date}, category={category})")
        
        # Build query filter
        query = {"user_id": user_id}
        
        # Add date range filter
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        # Add category filter
        if category:
            query["category"] = category
        
        # Execute query and convert cursor to list
        cursor = db.transactions.find(query)
        transactions = await cursor.to_list(length=None)
        
        # Convert MongoDB ObjectId to string for JSON serialization
        for txn in transactions:
            if "_id" in txn:
                txn["_id"] = str(txn["_id"])
        
        # Sort by timestamp (newest first)
        transactions_sorted = sorted(
            transactions,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        logger.info(f"Found {len(transactions_sorted)} transactions for user {user_id}")
        return transactions_sorted
    
    except Exception as e:
        logger.error(f"Error getting transactions for user {user_id}: {e}", exc_info=True)
        return []


async def create_transaction(db: Any, txn: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert new transaction.
    
    Generates transaction_id if not provided and adds timestamp if missing.
    Supports both MockDatabase and MongoDB backends.
    
    Args:
        db: Database instance (MockDatabase or AsyncIOMotorDatabase)
        txn: Transaction data dictionary
    
    Returns:
        Created transaction document
    
    Raises:
        ValueError: If required fields are missing
        Exception: If database operation fails
    
    Example:
        txn_data = {
            "user_id": "usr_1234567890",
            "amount": 450.0,
            "vendor": "Swiggy",
            "category": "food",
            "transaction_type": "debit",
            "source": "sms",
            "raw_sms_text": "Rs 450 debited from A/c XX1234..."
        }
        created_txn = await create_transaction(db, txn_data)
    """
    try:
        # Validate required fields
        required_fields = ["user_id", "amount", "vendor", "category", "transaction_type", "source"]
        missing_fields = [field for field in required_fields if field not in txn]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        logger.debug(f"Creating transaction for user {txn['user_id']}: "
                    f"{txn['transaction_type']} {txn['amount']} at {txn['vendor']}")
        
        # Generate transaction_id if not provided
        if "transaction_id" not in txn:
            timestamp_str = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
            txn["transaction_id"] = f"txn_{txn['user_id'][-10:]}_{timestamp_str}"
        
        # Add timestamp if not provided
        if "timestamp" not in txn:
            txn["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Ensure metadata field exists
        if "metadata" not in txn:
            txn["metadata"] = {}
        
        # Insert transaction
        result = await db.transactions.insert_one(txn)
        
        # Convert MongoDB ObjectId to string for JSON serialization
        if "_id" in txn:
            txn["_id"] = str(txn["_id"])
        
        logger.info(f"Created transaction {txn['transaction_id']} for user {txn['user_id']}")
        
        return txn
    
    except ValueError as e:
        logger.error(f"Validation error creating transaction: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating transaction: {e}", exc_info=True)
        raise
