"""
Core Configuration Module

Purpose:
    Centralized configuration management for the KIVI Backend system.
    Loads environment variables and exports configuration constants for use
    throughout the application.

Dependencies:
    - os: Environment variable access
    - python-dotenv: Load .env file

Usage:
    from app.config.config import MONGO_URI, JWT_SECRET, WHATSAPP_TOKEN
    
    # Use configuration constants
    client = AsyncIOMotorClient(MONGO_URI)
    token = jwt.encode(payload, JWT_SECRET)

Reference:
    Project brief: /mnt/data/MumbaiHacks 2025.pdf
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# WhatsApp Configuration
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "placeholder")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "placeholder")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "kivi-verify-token")

# AI Provider Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

# Project Reference
PROJECT_BRIEF = "/mnt/data/MumbaiHacks 2025.pdf"
