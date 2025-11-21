"""
Date and time utility functions.

This module provides functions for working with dates and timestamps,
including ISO format conversion, date parsing, and date range calculations.

Dependencies:
    - datetime (standard library)

Example Usage:
    from app.utils.date_utils import now_iso, parse_date, get_week_range, get_month_range
    
    # Get current timestamp
    timestamp = now_iso()  # "2025-01-20T14:30:00Z"
    
    # Parse date string
    dt = parse_date("2025-01-20")
    
    # Get week range
    start, end = get_week_range()  # ("2025-01-13T00:00:00Z", "2025-01-19T23:59:59Z")
    
    # Get month range
    start, end = get_month_range()  # ("2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z")
"""

from datetime import datetime, timedelta
from typing import Tuple


def now_iso() -> str:
    """
    Get current timestamp in ISO 8601 format.
    
    Returns:
        Current timestamp as ISO 8601 string with 'Z' suffix
    
    Example:
        >>> now_iso()
        '2025-01-20T14:30:00Z'
    """
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_date(date_str: str) -> datetime:
    """
    Parse date string in various formats to datetime object.
    
    Supports formats:
        - ISO 8601: "2025-01-20T14:30:00Z"
        - Date only: "2025-01-20"
        - Indian format: "20-Jan-25", "20-01-2025"
        - Slash format: "20/01/2025"
    
    Args:
        date_str: Date string to parse
    
    Returns:
        datetime object
    
    Raises:
        ValueError: If date string cannot be parsed
    
    Example:
        >>> parse_date("2025-01-20")
        datetime.datetime(2025, 1, 20, 0, 0)
        >>> parse_date("20-Jan-25")
        datetime.datetime(2025, 1, 20, 0, 0)
    """
    # List of date formats to try
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",      # ISO 8601 with Z
        "%Y-%m-%dT%H:%M:%S",       # ISO 8601 without Z
        "%Y-%m-%d",                # Date only
        "%d-%b-%y",                # 20-Jan-25
        "%d-%m-%Y",                # 20-01-2025
        "%d/%m/%Y",                # 20/01/2025
        "%Y/%m/%d",                # 2025/01/20
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # If no format matches, raise error
    raise ValueError(f"Unable to parse date string: {date_str}")


def get_week_range() -> Tuple[str, str]:
    """
    Get start and end timestamps for the current week (Monday to Sunday).
    
    Returns:
        Tuple of (start_timestamp, end_timestamp) in ISO 8601 format
    
    Example:
        >>> get_week_range()
        ('2025-01-13T00:00:00Z', '2025-01-19T23:59:59Z')
    """
    now = datetime.utcnow()
    
    # Get Monday of current week (weekday 0 = Monday)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get Sunday of current week
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return (
        start_of_week.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_of_week.strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def get_month_range() -> Tuple[str, str]:
    """
    Get start and end timestamps for the current month.
    
    Returns:
        Tuple of (start_timestamp, end_timestamp) in ISO 8601 format
    
    Example:
        >>> get_month_range()
        ('2025-01-01T00:00:00Z', '2025-01-31T23:59:59Z')
    """
    now = datetime.utcnow()
    
    # First day of current month
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Last day of current month
    # Get first day of next month, then subtract 1 second
    if now.month == 12:
        next_month = start_of_month.replace(year=now.year + 1, month=1)
    else:
        next_month = start_of_month.replace(month=now.month + 1)
    
    end_of_month = next_month - timedelta(seconds=1)
    
    return (
        start_of_month.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_of_month.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
