"""
SMS Parser Service

Purpose:
    Parse SMS messages from various banks to extract transaction details.
    Supports multiple SMS formats and handles both debit and credit transactions.

Dependencies:
    - re (regex for pattern matching)
    - datetime (for timestamp parsing)

Example Usage:
    from app.services.sms_parser import parse_sms
    
    sms_text = "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy"
    result = parse_sms(sms_text)
    # Returns: {
    #     "amount": 450.0,
    #     "vendor": "Swiggy",
    #     "timestamp": "2025-01-20T00:00:00Z",
    #     "transaction_type": "debit"
    # }
"""

import re
from datetime import datetime
from typing import Optional


def parse_sms(text: str) -> dict:
    """
    Extract transaction details from SMS text.
    
    Handles multiple SMS formats from different banks including:
    - HDFC, ICICI, SBI, Axis, Kotak, PNB, and other major banks
    - UPI payment notifications
    - Debit/Credit card transactions
    - Net banking transactions
    
    Args:
        text: Raw SMS message text
    
    Returns:
        Dictionary with extracted fields:
        {
            "amount": float,
            "vendor": str,
            "timestamp": str (ISO 8601 format),
            "transaction_type": "debit" | "credit"
        }
    """
    if not text:
        return {
            "amount": 0.0,
            "vendor": "Unknown",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "transaction_type": "debit"
        }
    
    # Extract amount
    amount = _extract_amount(text)
    
    # Extract vendor/merchant name
    vendor = _extract_vendor(text)
    
    # Extract timestamp
    timestamp = _extract_timestamp(text)
    
    # Determine transaction type (debit/credit)
    transaction_type = _extract_transaction_type(text)
    
    return {
        "amount": amount,
        "vendor": vendor,
        "timestamp": timestamp,
        "transaction_type": transaction_type
    }


def _extract_amount(text: str) -> float:
    """
    Extract transaction amount from SMS text.
    
    Patterns handled:
    - Rs 450, Rs. 450, INR 450
    - Rs.450.00, Rs 450.50
    - 450 Rs, 450.00 INR
    - Amount: 450, Amt: Rs 450
    """
    # Pattern 1: Rs/INR followed by amount (most common)
    # Matches: Rs 450, Rs. 450.00, INR 450, Rs.450
    pattern1 = r'(?:Rs\.?|INR|₹)\s*(\d+(?:,\d+)*(?:\.\d{2})?)'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        return float(amount_str)
    
    # Pattern 2: Amount followed by Rs/INR
    # Matches: 450 Rs, 450.00 INR
    pattern2 = r'(\d+(?:,\d+)*(?:\.\d{2})?)\s*(?:Rs\.?|INR|₹)'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        return float(amount_str)
    
    # Pattern 3: Amount with label
    # Matches: Amount: 450, Amt: Rs 450, Amount Rs 450
    pattern3 = r'(?:Amount|Amt|AMT)[\s:]*(?:Rs\.?|INR|₹)?\s*(\d+(?:,\d+)*(?:\.\d{2})?)'
    match = re.search(pattern3, text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        return float(amount_str)
    
    # Pattern 4: Generic number extraction (fallback)
    # Matches any number that looks like currency (with optional decimals)
    pattern4 = r'(\d+(?:,\d+)*(?:\.\d{2})?)'
    match = re.search(pattern4, text)
    if match:
        amount_str = match.group(1).replace(',', '')
        return float(amount_str)
    
    return 0.0


def _extract_vendor(text: str) -> str:
    """
    Extract vendor/merchant name from SMS text.
    
    Patterns handled:
    - "to Swiggy", "at Swiggy", "from Swiggy"
    - "paid to Swiggy", "payment to Swiggy"
    - "VPA: merchant@paytm", "UPI: merchant@upi"
    - "merchant name: Swiggy"
    - Card transactions with merchant codes
    """
    # Pattern 1: "to/at/from [Vendor]" (most specific, check first)
    # Matches: to Swiggy, at Amazon, from Zomato
    # Use word boundary and stop at common delimiters
    pattern1 = r'(?:to|at|from)\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)?)(?:\s+(?:on|for|via|dated|using|through|VPA|UPI)|\s*$)'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        vendor = match.group(1).strip()
        return vendor
    
    # Pattern 2: "paid to [Vendor]", "payment to/from [Vendor]", "received from [Vendor]"
    # Matches: paid to merchant@paytm, payment from Swiggy, received from Zomato
    pattern2 = r'(?:paid|payment|received)\s+(?:to|from)\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)?)(?:\s+(?:on|for|via|dated)|\s*$)'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        vendor = match.group(1).strip()
        return vendor
    
    # Pattern 3: UPI VPA extraction
    # Matches: VPA: merchant@paytm, merchant@upi
    pattern3 = r'([a-zA-Z0-9\-\.]+)@(?:paytm|upi|ybl|okaxis|okhdfcbank|okicici)'
    match = re.search(pattern3, text, re.IGNORECASE)
    if match:
        vendor = match.group(1).strip()
        # Capitalize first letter
        return vendor.capitalize()
    
    # Pattern 4: "merchant [name]", "merchant name: [name]"
    # Matches: merchant Swiggy, merchant name: Amazon
    pattern4 = r'merchant(?:\s+name)?[\s:]+([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)?)(?:\s+(?:on|for)|\s*$)'
    match = re.search(pattern4, text, re.IGNORECASE)
    if match:
        vendor = match.group(1).strip()
        return vendor
    
    # Pattern 5: Look for capitalized words (likely vendor names)
    # Matches: Swiggy, Amazon, Zomato (standalone capitalized words)
    # Exclude common bank-related words
    pattern5 = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
    matches = re.findall(pattern5, text)
    if matches:
        # Filter out common bank-related words and short words
        excluded_words = {'Account', 'Card', 'Bank', 'Transaction', 'Payment', 'Transfer', 
                         'Debit', 'Credit', 'Balance', 'Available', 'Amount', 'Date', 
                         'Your', 'The', 'From', 'For', 'Via', 'Using', 'Through', 'Jan',
                         'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
                         'Nov', 'Dec', 'Rs', 'Inr'}
        for match in matches:
            if match not in excluded_words and len(match) > 2:
                return match
    
    return "Unknown"


def _extract_timestamp(text: str) -> str:
    """
    Extract transaction timestamp from SMS text.
    
    Patterns handled:
    - "on 20-Jan-25", "on 20/01/2025", "on 20.01.25"
    - "dated 20-Jan-2025", "date: 20/01/25"
    - "at 19:30 on 20-Jan-25"
    - ISO format timestamps
    
    Returns ISO 8601 formatted timestamp string.
    """
    current_year = datetime.now().year
    
    # Pattern 1: "on DD-MMM-YY" or "on DD-MMM-YYYY"
    # Matches: on 20-Jan-25, on 20-Jan-2025
    pattern1 = r'on\s+(\d{1,2})-([A-Za-z]{3})-(\d{2,4})'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month_str = match.group(2)
        year = int(match.group(3))
        
        # Convert 2-digit year to 4-digit
        if year < 100:
            year = 2000 + year
        
        # Parse month name
        month = _parse_month(month_str)
        
        try:
            dt = datetime(year, month, day)
            return dt.isoformat() + "Z"
        except ValueError:
            pass
    
    # Pattern 2: "on DD/MM/YY" or "on DD/MM/YYYY"
    # Matches: on 20/01/25, on 20/01/2025
    pattern2 = r'on\s+(\d{1,2})[/\.](\d{1,2})[/\.](\d{2,4})'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        
        # Convert 2-digit year to 4-digit
        if year < 100:
            year = 2000 + year
        
        try:
            dt = datetime(year, month, day)
            return dt.isoformat() + "Z"
        except ValueError:
            pass
    
    # Pattern 3: "dated DD-MMM-YYYY" or "date: DD/MM/YY"
    # Matches: dated 20-Jan-2025, date: 20/01/25
    pattern3 = r'(?:dated|date)[\s:]+(\d{1,2})[-/\.]([A-Za-z0-9]{2,3})[-/\.](\d{2,4})'
    match = re.search(pattern3, text, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month_or_name = match.group(2)
        year = int(match.group(3))
        
        # Convert 2-digit year to 4-digit
        if year < 100:
            year = 2000 + year
        
        # Check if month is numeric or name
        if month_or_name.isdigit():
            month = int(month_or_name)
        else:
            month = _parse_month(month_or_name)
        
        try:
            dt = datetime(year, month, day)
            return dt.isoformat() + "Z"
        except ValueError:
            pass
    
    # Pattern 4: Time with date "at HH:MM on DD-MMM-YY"
    # Matches: at 19:30 on 20-Jan-25
    pattern4 = r'at\s+(\d{1,2}):(\d{2}).*?on\s+(\d{1,2})-([A-Za-z]{3})-(\d{2,4})'
    match = re.search(pattern4, text, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        day = int(match.group(3))
        month_str = match.group(4)
        year = int(match.group(5))
        
        # Convert 2-digit year to 4-digit
        if year < 100:
            year = 2000 + year
        
        month = _parse_month(month_str)
        
        try:
            dt = datetime(year, month, day, hour, minute)
            return dt.isoformat() + "Z"
        except ValueError:
            pass
    
    # Fallback: Return current timestamp
    return datetime.utcnow().isoformat() + "Z"


def _extract_transaction_type(text: str) -> str:
    """
    Determine if transaction is debit or credit.
    
    Keywords for debit: debited, debit, spent, paid, payment, withdrawn, purchase
    Keywords for credit: credited, credit, received, deposited, refund
    """
    text_lower = text.lower()
    
    # Check for credit keywords
    credit_keywords = ['credited', 'credit', 'received', 'deposited', 'refund', 'cashback']
    for keyword in credit_keywords:
        if keyword in text_lower:
            return "credit"
    
    # Check for debit keywords
    debit_keywords = ['debited', 'debit', 'spent', 'paid', 'payment', 'withdrawn', 'purchase']
    for keyword in debit_keywords:
        if keyword in text_lower:
            return "debit"
    
    # Default to debit if unclear
    return "debit"


def _parse_month(month_str: str) -> int:
    """
    Convert month name/abbreviation to month number.
    
    Args:
        month_str: Month name or abbreviation (e.g., "Jan", "January", "01")
    
    Returns:
        Month number (1-12)
    """
    month_map = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }
    
    month_lower = month_str.lower()
    return month_map.get(month_lower, 1)
