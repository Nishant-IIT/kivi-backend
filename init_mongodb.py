"""
MongoDB Database Initialization Script

Purpose:
    Initialize the kivi_db database with required collections and indexes.
    Creates collections: users, transactions, message_logs, sessions, notifications, user_rules

Usage:
    python init_mongodb.py
"""

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB URI from environment
uri = os.getenv("MONGO_URI")

if not uri:
    print("✗ Error: MONGO_URI not found in .env file")
    exit(1)

# Create client
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    # Test connection
    client.admin.command('ping')
    print("✓ Connected to MongoDB")
    
    # Get or create kivi_db database
    db = client.kivi_db
    print("✓ Using database: kivi_db")
    
    # Define collections to create
    collections = [
        "users",
        "transactions", 
        "message_logs",
        "sessions",
        "notifications",
        "user_rules"
    ]
    
    # Get existing collections
    existing_collections = db.list_collection_names()
    
    # Create collections if they don't exist
    for collection_name in collections:
        if collection_name not in existing_collections:
            db.create_collection(collection_name)
            print(f"✓ Created collection: {collection_name}")
        else:
            print(f"  Collection already exists: {collection_name}")
    
    # Create indexes
    print("\n✓ Creating indexes...")
    
    # Users collection indexes
    db.users.create_index("phone", unique=True)
    print("  - users.phone (unique)")
    
    # Transactions collection indexes
    db.transactions.create_index("user_id")
    db.transactions.create_index("timestamp")
    print("  - transactions.user_id")
    print("  - transactions.timestamp")
    
    # Message logs collection indexes
    db.message_logs.create_index("user_id")
    db.message_logs.create_index("timestamp")
    print("  - message_logs.user_id")
    print("  - message_logs.timestamp")
    
    # Sessions collection indexes
    db.sessions.create_index("user_id")
    db.sessions.create_index("session_id", unique=True)
    print("  - sessions.user_id")
    print("  - sessions.session_id (unique)")
    
    print("\n✓ Database initialization complete!")
    print(f"✓ Collections in kivi_db: {db.list_collection_names()}")
    
except Exception as e:
    print(f"✗ Error: {e}")
finally:
    client.close()
