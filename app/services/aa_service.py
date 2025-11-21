"""
Account Aggregator Service Placeholder

Purpose:
    Provides placeholder functions for Account Aggregator (AA) integration.
    Returns sample gig worker financial data with multiple income sources
    and transactions. Includes normalization function to transform AA data
    to internal format.

Dependencies:
    - None (placeholder implementation)

Usage:
    from app.services.aa_service import fetch_aa_data, normalize_aa_data
    
    # Fetch sample AA data for user
    aa_data = await fetch_aa_data("usr_1234567890")
    
    # Normalize to internal format
    normalized = normalize_aa_data(aa_data)

Future Integration:
    This is a placeholder implementation. In production, this module will:
    - Integrate with real Account Aggregator APIs (Sahamati framework)
    - Handle OAuth consent flow for financial data access
    - Fetch real-time bank account data, transactions, and balances
    - Support multiple financial institutions and data providers
    - Implement secure data encryption and compliance requirements

Reference:
    Requirements: 19.2, 19.3
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("kivi.aa")


async def fetch_aa_data(user_id: str) -> Dict[str, Any]:
    """
    Fetch Account Aggregator data for user.
    
    PLACEHOLDER IMPLEMENTATION: Returns sample gig worker financial data
    with multiple income sources (Swiggy, Zomato, Dunzo, freelance work)
    and realistic transaction patterns.
    
    Future Implementation:
    - Connect to real AA API endpoints (Sahamati framework)
    - Handle user consent and OAuth flow
    - Fetch data from linked bank accounts
    - Support multiple financial institutions
    - Implement data refresh and caching strategies
    
    Args:
        user_id: User identifier
    
    Returns:
        Dictionary containing:
        - accounts: List of linked bank accounts with balances
        - transactions: List of recent transactions from all accounts
        - income_sources: Breakdown of income by platform/source
        - metadata: Additional financial information
    
    Example:
        aa_data = await fetch_aa_data("usr_1234567890")
        print(f"Total balance: {aa_data['total_balance']}")
        print(f"Income sources: {len(aa_data['income_sources'])}")
    """
    logger.info(f"Fetching AA data for user {user_id} (using sample data)")
    
    # TODO: Replace with real AA API integration
    # Example real implementation:
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         "https://api.sahamati.org.in/v1/accounts/fetch",
    #         headers={"Authorization": f"Bearer {aa_token}"},
    #         json={"user_id": user_id, "consent_id": consent_id}
    #     )
    #     return response.json()
    
    # Generate sample data for gig worker
    now = datetime.utcnow()
    
    # Sample bank accounts
    accounts = [
        {
            "account_id": "acc_hdfc_001",
            "bank_name": "HDFC Bank",
            "account_number": "XXXX1234",
            "account_type": "savings",
            "balance": 12000.0,
            "currency": "INR",
            "last_updated": now.isoformat() + "Z"
        },
        {
            "account_id": "acc_paytm_001",
            "bank_name": "Paytm Payments Bank",
            "account_number": "XXXX5678",
            "account_type": "wallet",
            "balance": 3500.0,
            "currency": "INR",
            "last_updated": now.isoformat() + "Z"
        }
    ]
    
    # Sample transactions (last 30 days) - gig worker pattern
    transactions = []
    
    # Swiggy earnings (frequent small credits)
    for i in range(15):
        day_offset = i * 2
        transactions.append({
            "transaction_id": f"txn_swiggy_{i:03d}",
            "account_id": "acc_paytm_001",
            "date": (now - timedelta(days=day_offset)).isoformat() + "Z",
            "description": f"Swiggy Delivery Payment - Order #{1000 + i}",
            "amount": 180.0 + (i * 20),  # Variable earnings
            "type": "credit",
            "category": "income",
            "vendor": "Swiggy",
            "balance_after": 3500.0
        })
    
    # Zomato earnings (less frequent, larger amounts)
    for i in range(8):
        day_offset = i * 3 + 1
        transactions.append({
            "transaction_id": f"txn_zomato_{i:03d}",
            "account_id": "acc_paytm_001",
            "date": (now - timedelta(days=day_offset)).isoformat() + "Z",
            "description": f"Zomato Delivery Payment - Batch #{500 + i}",
            "amount": 450.0 + (i * 30),
            "type": "credit",
            "category": "income",
            "vendor": "Zomato",
            "balance_after": 3500.0
        })
    
    # Dunzo earnings (occasional)
    for i in range(4):
        day_offset = i * 7 + 2
        transactions.append({
            "transaction_id": f"txn_dunzo_{i:03d}",
            "account_id": "acc_paytm_001",
            "date": (now - timedelta(days=day_offset)).isoformat() + "Z",
            "description": f"Dunzo Task Payment - #{200 + i}",
            "amount": 120.0 + (i * 15),
            "type": "credit",
            "category": "income",
            "vendor": "Dunzo",
            "balance_after": 3500.0
        })
    
    # Freelance work (occasional larger payments)
    transactions.append({
        "transaction_id": "txn_freelance_001",
        "account_id": "acc_hdfc_001",
        "date": (now - timedelta(days=5)).isoformat() + "Z",
        "description": "Freelance Design Project - Client Payment",
        "amount": 5000.0,
        "type": "credit",
        "category": "income",
        "vendor": "Freelance Client",
        "balance_after": 12000.0
    })
    
    # Expenses - Fuel (frequent for delivery work)
    for i in range(10):
        day_offset = i * 3
        transactions.append({
            "transaction_id": f"txn_fuel_{i:03d}",
            "account_id": "acc_hdfc_001",
            "date": (now - timedelta(days=day_offset)).isoformat() + "Z",
            "description": f"Petrol Pump - Fuel",
            "amount": -250.0,
            "type": "debit",
            "category": "transport",
            "vendor": "Indian Oil",
            "balance_after": 12000.0
        })
    
    # Expenses - Food
    for i in range(12):
        day_offset = i * 2 + 1
        transactions.append({
            "transaction_id": f"txn_food_{i:03d}",
            "account_id": "acc_hdfc_001",
            "date": (now - timedelta(days=day_offset)).isoformat() + "Z",
            "description": f"Food Purchase",
            "amount": -150.0 - (i * 10),
            "type": "debit",
            "category": "food",
            "vendor": "Local Restaurant",
            "balance_after": 12000.0
        })
    
    # Expenses - Bike maintenance
    transactions.append({
        "transaction_id": "txn_maintenance_001",
        "account_id": "acc_hdfc_001",
        "date": (now - timedelta(days=15)).isoformat() + "Z",
        "description": "Bike Service and Repair",
        "amount": -1200.0,
        "type": "debit",
        "category": "transport",
        "vendor": "Honda Service Center",
        "balance_after": 12000.0
    })
    
    # Expenses - Rent
    transactions.append({
        "transaction_id": "txn_rent_001",
        "account_id": "acc_hdfc_001",
        "date": (now - timedelta(days=3)).isoformat() + "Z",
        "description": "Monthly Rent Payment",
        "amount": -8000.0,
        "type": "debit",
        "category": "bills",
        "vendor": "Landlord",
        "balance_after": 12000.0
    })
    
    # Expenses - Mobile recharge
    transactions.append({
        "transaction_id": "txn_mobile_001",
        "account_id": "acc_hdfc_001",
        "date": (now - timedelta(days=10)).isoformat() + "Z",
        "description": "Mobile Recharge - Jio",
        "amount": -399.0,
        "type": "debit",
        "category": "bills",
        "vendor": "Jio",
        "balance_after": 12000.0
    })
    
    # Sort transactions by date (newest first)
    transactions.sort(key=lambda x: x["date"], reverse=True)
    
    # Calculate income sources breakdown
    income_sources = {
        "Swiggy": sum(t["amount"] for t in transactions if t["vendor"] == "Swiggy"),
        "Zomato": sum(t["amount"] for t in transactions if t["vendor"] == "Zomato"),
        "Dunzo": sum(t["amount"] for t in transactions if t["vendor"] == "Dunzo"),
        "Freelance": sum(t["amount"] for t in transactions if "Freelance" in t["vendor"])
    }
    
    # Calculate total balance
    total_balance = sum(acc["balance"] for acc in accounts)
    
    # Calculate income and expense totals
    total_income = sum(t["amount"] for t in transactions if t["type"] == "credit")
    total_expenses = abs(sum(t["amount"] for t in transactions if t["type"] == "debit"))
    
    aa_data = {
        "user_id": user_id,
        "accounts": accounts,
        "transactions": transactions,
        "income_sources": income_sources,
        "total_balance": total_balance,
        "total_income_30d": total_income,
        "total_expenses_30d": total_expenses,
        "metadata": {
            "data_source": "sample",
            "fetch_timestamp": now.isoformat() + "Z",
            "account_count": len(accounts),
            "transaction_count": len(transactions),
            "date_range": {
                "start": (now - timedelta(days=30)).isoformat() + "Z",
                "end": now.isoformat() + "Z"
            }
        }
    }
    
    logger.debug(f"Generated sample AA data: {len(accounts)} accounts, "
                f"{len(transactions)} transactions, {len(income_sources)} income sources")
    logger.info(f"Total balance: ₹{total_balance:.2f}, "
               f"Income: ₹{total_income:.2f}, Expenses: ₹{total_expenses:.2f}")
    
    return aa_data


def normalize_aa_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Account Aggregator data to internal format.
    
    Converts AA API response format to KIVI internal transaction and
    financial summary format. Handles data mapping, type conversion,
    and field normalization.
    
    Future Implementation:
    - Support multiple AA provider formats
    - Handle different bank data schemas
    - Implement data validation and error handling
    - Support incremental data updates
    
    Args:
        raw_data: Raw AA data from fetch_aa_data()
    
    Returns:
        Dictionary containing:
        - transactions: List of normalized transactions
        - financial_summary: Aggregated financial metrics
        - income_sources: Income breakdown by source
    
    Example:
        raw_aa_data = await fetch_aa_data("usr_1234567890")
        normalized = normalize_aa_data(raw_aa_data)
        
        # Use normalized data to update user profile
        user["financial_summary"] = normalized["financial_summary"]
    """
    logger.debug(f"Normalizing AA data for user {raw_data.get('user_id', 'unknown')}")
    
    # Extract transactions and convert to internal format
    normalized_transactions = []
    
    for txn in raw_data.get("transactions", []):
        # Map AA transaction format to internal format
        normalized_txn = {
            "transaction_id": txn.get("transaction_id"),
            "user_id": raw_data.get("user_id"),
            "amount": abs(txn.get("amount", 0.0)),
            "vendor": txn.get("vendor", "Unknown"),
            "category": txn.get("category", "others"),
            "transaction_type": "credit" if txn.get("type") == "credit" else "debit",
            "timestamp": txn.get("date"),
            "source": "aa",
            "raw_sms_text": None,
            "metadata": {
                "account_id": txn.get("account_id"),
                "description": txn.get("description"),
                "balance_after": txn.get("balance_after")
            }
        }
        normalized_transactions.append(normalized_txn)
    
    # Build financial summary
    financial_summary = {
        "current_balance": raw_data.get("total_balance", 0.0),
        "avg_monthly_income": raw_data.get("total_income_30d", 0.0),
        "monthly_expenses": raw_data.get("total_expenses_30d", 0.0),
        "income_volatility": _calculate_income_volatility(raw_data.get("transactions", [])),
        "last_30_days_income": raw_data.get("total_income_30d", 0.0),
        "income_sources": raw_data.get("income_sources", {})
    }
    
    # Calculate category breakdown for expenses
    category_breakdown = {}
    for txn in raw_data.get("transactions", []):
        if txn.get("type") == "debit":
            category = txn.get("category", "others")
            amount = abs(txn.get("amount", 0.0))
            category_breakdown[category] = category_breakdown.get(category, 0.0) + amount
    
    normalized_data = {
        "transactions": normalized_transactions,
        "financial_summary": financial_summary,
        "income_sources": raw_data.get("income_sources", {}),
        "category_breakdown": category_breakdown,
        "accounts": raw_data.get("accounts", []),
        "metadata": raw_data.get("metadata", {})
    }
    
    logger.info(f"Normalized {len(normalized_transactions)} transactions, "
               f"{len(raw_data.get('income_sources', {}))} income sources")
    
    return normalized_data


def _calculate_income_volatility(transactions: List[Dict[str, Any]]) -> str:
    """
    Calculate income volatility based on transaction patterns.
    
    Analyzes income transaction frequency and amount variation to
    determine volatility level (low, medium, high).
    
    Args:
        transactions: List of transaction dictionaries
    
    Returns:
        Volatility level: "low", "medium", or "high"
    """
    # Filter income transactions
    income_txns = [t for t in transactions if t.get("type") == "credit"]
    
    if len(income_txns) < 2:
        return "medium"
    
    # Calculate coefficient of variation
    amounts = [t.get("amount", 0.0) for t in income_txns]
    avg_amount = sum(amounts) / len(amounts)
    
    if avg_amount == 0:
        return "medium"
    
    variance = sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)
    std_dev = variance ** 0.5
    cv = std_dev / avg_amount
    
    # Classify volatility
    if cv < 0.3:
        return "low"
    elif cv < 0.6:
        return "medium"
    else:
        return "high"
