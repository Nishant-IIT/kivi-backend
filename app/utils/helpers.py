"""
Utility helper functions for common operations.

This module provides general-purpose utility functions for currency formatting,
safe dictionary access, and unique ID generation.

Dependencies:
    - uuid (standard library)
    - time (standard library)
    - random (standard library)

Example Usage:
    from app.utils.helpers import format_currency, safe_get, generate_id
    
    # Format currency
    amount_str = format_currency(1234.56)  # "₹1,234.56"
    
    # Safe dictionary access
    value = safe_get(user_data, "email", "no-email@example.com")
    
    # Generate unique ID
    user_id = generate_id("usr")  # "usr_1737417600_a3f2"
"""

import uuid


def format_currency(amount: float, currency: str = "INR") -> str:
    """
    Format numeric amount with currency symbol and proper formatting.
    
    Args:
        amount: Numeric amount to format
        currency: Currency code (default: "INR")
    
    Returns:
        Formatted currency string with symbol and comma separators
    
    Example:
        >>> format_currency(1234.56)
        '₹1,234.56'
        >>> format_currency(1000000.00)
        '₹10,00,000.00'
    """
    currency_symbols = {
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    # Format with 2 decimal places and comma separators
    formatted = f"{amount:,.2f}"
    
    return f"{symbol}{formatted}"


def safe_get(d: dict, key: str, default=None):
    """
    Safely retrieve value from dictionary with default fallback.
    
    Args:
        d: Dictionary to access
        key: Key to retrieve
        default: Default value if key not found (default: None)
    
    Returns:
        Value from dictionary or default if key doesn't exist
    
    Example:
        >>> user = {"name": "Rahul", "phone": "+919876543210"}
        >>> safe_get(user, "email", "no-email@example.com")
        'no-email@example.com'
        >>> safe_get(user, "name", "Unknown")
        'Rahul'
    """
    try:
        return d.get(key, default)
    except (AttributeError, TypeError):
        return default


def generate_id(prefix: str = "") -> str:
    """
    Generate unique identifier using UUID with optional prefix.
    
    Args:
        prefix: Optional prefix for the ID (e.g., "usr", "txn", "msg")
    
    Returns:
        Unique ID string in format: prefix_uuid or uuid
    
    Example:
        >>> generate_id("usr")
        'usr_a3f2b8e9-c4d1-4e5f-9a1b-2c3d4e5f6a7b'
        >>> generate_id("txn")
        'txn_b8e9c4d1-e5f6-4a7b-8c9d-0e1f2a3b4c5d'
        >>> generate_id()
        'c4d1e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f'
    """
    unique_id = str(uuid.uuid4())
    
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id
