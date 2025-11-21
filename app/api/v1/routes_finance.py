"""
Finance Routes Module

Purpose:
    Provides endpoints for financial transaction management, SMS parsing,
    dashboard data, and periodic reports. Supports transaction tracking,
    categorization, and analysis for gig workers.

Dependencies:
    - fastapi: Web framework and routing
    - pydantic: Request/response validation
    - app.core.security: Authentication dependency
    - app.models.transaction_model: Transaction data access
    - app.models.user_model: User data access
    - app.services.sms_parser: SMS text parsing
    - app.services.expense_analyzer: Transaction categorization and analysis
    - app.services.nudge_engine: Rule evaluation and nudges
    - app.db.mongodb: Database connection

Endpoints:
    GET /transactions
        Retrieve transaction history with optional filters
        Query params: start_date, end_date, category
        
    POST /transactions
        Create manual transaction entry
        
    POST /transactions/sms
        Parse SMS text and create transaction
        
    GET /dashboard
        Get dashboard summary with balance, spending, categories, budgets
        
    GET /reports/weekly
        Get weekly spending report
        
    GET /reports/monthly
        Get monthly spending report

Usage:
    # Get transactions
    curl -X GET "http://localhost:8000/api/v1/transactions?category=food" \
      -H "Authorization: Bearer <token>"
    
    # Parse SMS
    curl -X POST http://localhost:8000/api/v1/transactions/sms \
      -H "Authorization: Bearer <token>" \
      -H "Content-Type: application/json" \
      -d '{"sms_text": "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy"}'

Reference:
    Requirements: 7.1, 7.2, 7.3, 7.5, 7.6, 7.7, 7.8, 22.1, 22.2, 22.3, 22.4
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.core.security import get_current_user
from app.models.transaction_model import (
    Transaction,
    get_transactions,
    create_transaction
)
from app.models.user_model import get_user_by_phone
from app.services.sms_parser import parse_sms
from app.services.expense_analyzer import (
    categorize_transaction,
    summarize_transactions,
    get_category_insights
)
from app.services.nudge_engine import (
    generate_nudges,
    generate_gig_worker_insights,
    evaluate_rules
)
from app.db.mongodb import get_db

# Logger for finance operations
logger = logging.getLogger("kivi.finance")

# Create router instance
router = APIRouter(prefix="/api/v1", tags=["finance"])


class TransactionCreateRequest(BaseModel):
    """
    Manual transaction creation request schema.
    
    Attributes:
        amount: Transaction amount
        vendor: Merchant/vendor name
        category: Transaction category (optional, will be auto-categorized if not provided)
        transaction_type: "debit" or "credit"
        timestamp: Transaction timestamp (optional, defaults to now)
        metadata: Additional metadata (optional)
    """
    amount: float = Field(..., description="Transaction amount", example=450.0)
    vendor: str = Field(..., description="Vendor/merchant name", example="Swiggy")
    category: Optional[str] = Field(None, description="Transaction category", example="food")
    transaction_type: str = Field(..., description="Transaction type", example="debit")
    timestamp: Optional[str] = Field(None, description="Transaction timestamp (ISO 8601)", example="2025-01-20T19:30:00Z")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class SMSParseRequest(BaseModel):
    """
    SMS parsing request schema.
    
    Attributes:
        sms_text: Raw SMS message text from bank/payment provider
    """
    sms_text: str = Field(..., description="Raw SMS message text", example="Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy")


class TransactionResponse(BaseModel):
    """Transaction response schema."""
    transaction_id: str
    user_id: str
    amount: float
    vendor: str
    category: str
    transaction_type: str
    timestamp: str
    source: str
    raw_sms_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    """Dashboard summary response schema."""
    balance: float
    monthly_spending: float
    category_breakdown: Dict[str, float]
    budgets: List[Dict[str, Any]]
    recent_transactions: List[Dict[str, Any]]
    nudges: List[str]


class WeeklyReportResponse(BaseModel):
    """Weekly report response schema."""
    week_start: str
    week_end: str
    total_spent: float
    total_earned: float
    net_change: float
    top_categories: List[Dict[str, Any]]
    comparison_to_previous_week: Dict[str, Any]
    transaction_count: int


class MonthlyReportResponse(BaseModel):
    """Monthly report response schema."""
    month: str
    year: int
    total_spent: float
    total_earned: float
    net_change: float
    category_trends: Dict[str, float]
    budget_adherence: List[Dict[str, Any]]
    daily_average: float
    transaction_count: int
    gig_worker_insights: Optional[Dict[str, Any]] = None


@router.get("/transactions", response_model=List[TransactionResponse], status_code=status.HTTP_200_OK)
async def get_transaction_history(
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601)", example="2025-01-01T00:00:00Z"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601)", example="2025-01-31T23:59:59Z"),
    category: Optional[str] = Query(None, description="Filter by category", example="food"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
) -> List[TransactionResponse]:
    """
    Retrieve transaction history with optional filters.
    
    Supports filtering by date range and category. Returns transactions
    sorted by timestamp (newest first).
    
    Args:
        start_date: Start date filter (optional)
        end_date: End date filter (optional)
        category: Category filter (optional)
        current_user: Authenticated user info (injected)
        db: Database instance (injected)
    
    Returns:
        List of transactions matching filters
    
    Example:
        GET /api/v1/transactions?start_date=2025-01-01T00:00:00Z&category=food
        Headers: Authorization: Bearer <token>
    """
    user_id = current_user["user_id"]
    
    logger.info(f"Fetching transactions for user {user_id} "
                f"(start={start_date}, end={end_date}, category={category})")
    
    try:
        # Get transactions from database
        transactions = await get_transactions(
            db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            category=category
        )
        
        logger.info(f"Retrieved {len(transactions)} transactions for user {user_id}")
        
        # Convert to response models
        return [TransactionResponse(**txn) for txn in transactions]
    
    except Exception as e:
        logger.error(f"Error fetching transactions for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching transactions"
        )


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_transaction(
    request: TransactionCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
) -> TransactionResponse:
    """
    Create manual transaction entry.
    
    Allows users to manually add transactions that weren't captured via SMS
    or Account Aggregator. Auto-categorizes if category not provided.
    
    Args:
        request: Transaction creation data
        current_user: Authenticated user info (injected)
        db: Database instance (injected)
    
    Returns:
        Created transaction
    
    Example:
        POST /api/v1/transactions
        Headers: Authorization: Bearer <token>
        Body:
        {
            "amount": 450.0,
            "vendor": "Swiggy",
            "transaction_type": "debit"
        }
    """
    user_id = current_user["user_id"]
    
    logger.info(f"Creating manual transaction for user {user_id}: "
                f"{request.transaction_type} {request.amount} at {request.vendor}")
    
    try:
        # Build transaction data
        txn_data = {
            "user_id": user_id,
            "amount": request.amount,
            "vendor": request.vendor,
            "category": request.category,
            "transaction_type": request.transaction_type,
            "source": "manual",
            "metadata": request.metadata or {}
        }
        
        # Add timestamp if provided
        if request.timestamp:
            txn_data["timestamp"] = request.timestamp
        
        # Auto-categorize if category not provided
        if not txn_data["category"]:
            txn_data["category"] = categorize_transaction(txn_data)
            logger.debug(f"Auto-categorized transaction as: {txn_data['category']}")
        
        # Create transaction
        created_txn = await create_transaction(db, txn_data)
        
        # Evaluate rules for notifications
        await evaluate_rules(db, user_id, created_txn)
        
        logger.info(f"Created manual transaction {created_txn['transaction_id']} for user {user_id}")
        
        return TransactionResponse(**created_txn)
    
    except ValueError as e:
        logger.error(f"Validation error creating transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error creating manual transaction for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating transaction"
        )


@router.post("/transactions/sms", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def parse_sms_transaction(
    request: SMSParseRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
) -> TransactionResponse:
    """
    Parse SMS text and create transaction.
    
    Extracts transaction details from bank SMS message, categorizes the
    transaction, creates a transaction record, and evaluates notification rules.
    
    Args:
        request: SMS parsing request with raw SMS text
        current_user: Authenticated user info (injected)
        db: Database instance (injected)
    
    Returns:
        Created transaction with parsed and categorized data
    
    Example:
        POST /api/v1/transactions/sms
        Headers: Authorization: Bearer <token>
        Body:
        {
            "sms_text": "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy"
        }
        
        Response:
        {
            "transaction_id": "txn_...",
            "user_id": "usr_...",
            "amount": 450.0,
            "vendor": "Swiggy",
            "category": "food",
            "transaction_type": "debit",
            "timestamp": "2025-01-20T00:00:00Z",
            "source": "sms",
            "raw_sms_text": "Rs 450 debited..."
        }
    """
    user_id = current_user["user_id"]
    
    logger.info(f"Parsing SMS transaction for user {user_id}")
    logger.debug(f"SMS text: {request.sms_text[:100]}...")
    
    try:
        # Step 1: Parse SMS text
        parsed_data = parse_sms(request.sms_text)
        logger.debug(f"Parsed SMS data: amount={parsed_data['amount']}, "
                    f"vendor={parsed_data['vendor']}, type={parsed_data['transaction_type']}")
        
        # Step 2: Build transaction data
        txn_data = {
            "user_id": user_id,
            "amount": parsed_data["amount"],
            "vendor": parsed_data["vendor"],
            "transaction_type": parsed_data["transaction_type"],
            "timestamp": parsed_data["timestamp"],
            "source": "sms",
            "raw_sms_text": request.sms_text,
            "metadata": {}
        }
        
        # Step 3: Classify transaction using expense analyzer
        txn_data["category"] = categorize_transaction(txn_data)
        logger.debug(f"Categorized transaction as: {txn_data['category']}")
        
        # Step 4: Create transaction record
        created_txn = await create_transaction(db, txn_data)
        logger.info(f"Created SMS transaction {created_txn['transaction_id']} for user {user_id}")
        
        # Step 5: Evaluate rules using nudge engine
        await evaluate_rules(db, user_id, created_txn)
        logger.debug(f"Evaluated rules for transaction {created_txn['transaction_id']}")
        
        return TransactionResponse(**created_txn)
    
    except ValueError as e:
        logger.error(f"Validation error parsing SMS: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid SMS format: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Error parsing SMS transaction for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while parsing SMS transaction"
        )


@router.get("/dashboard", response_model=DashboardResponse, status_code=status.HTTP_200_OK)
async def get_dashboard(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
) -> DashboardResponse:
    """
    Get dashboard summary with balance, spending, categories, and budgets.
    
    Provides comprehensive financial overview including:
    - Current balance
    - Monthly spending total
    - Category breakdown
    - Budget status
    - Recent transactions (last 10)
    - Personalized nudges
    
    Args:
        current_user: Authenticated user info (injected)
        db: Database instance (injected)
    
    Returns:
        Dashboard summary data
    
    Example:
        GET /api/v1/dashboard
        Headers: Authorization: Bearer <token>
        
        Response:
        {
            "balance": 12000.0,
            "monthly_spending": 8500.0,
            "category_breakdown": {
                "food": 3200.0,
                "transport": 2800.0,
                "fuel": 1500.0
            },
            "budgets": [...],
            "recent_transactions": [...],
            "nudges": [...]
        }
    """
    user_id = current_user["user_id"]
    phone = current_user["phone"]
    
    logger.info(f"Fetching dashboard for user {user_id}")
    
    try:
        # Get user profile
        user = await get_user_by_phone(db, phone)
        
        if not user:
            logger.warning(f"User profile not found for user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Get current month date range
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start_str = month_start.isoformat() + "Z"
        month_end_str = now.isoformat() + "Z"
        
        # Get current month transactions
        transactions = await get_transactions(
            db,
            user_id=user_id,
            start_date=month_start_str,
            end_date=month_end_str
        )
        
        logger.debug(f"Retrieved {len(transactions)} transactions for current month")
        
        # Calculate category breakdown
        summary = summarize_transactions(transactions)
        category_breakdown = {
            k: v for k, v in summary.items()
            if k not in ["total", "transaction_count"] and v > 0
        }
        
        # Get financial summary from user profile
        financial_summary = user.get("financial_summary", {})
        balance = financial_summary.get("current_balance", 0.0)
        monthly_spending = summary.get("total", 0.0)
        
        # Get budgets
        budgets = user.get("budgets", [])
        
        # Get recent transactions (last 10)
        all_transactions = await get_transactions(db, user_id=user_id)
        recent_transactions = all_transactions[:10]
        
        # Generate nudges
        nudges = generate_nudges(user, transactions)
        
        logger.info(f"Dashboard generated for user {user_id}: "
                   f"balance={balance}, spending={monthly_spending}, "
                   f"{len(nudges)} nudges")
        
        return DashboardResponse(
            balance=balance,
            monthly_spending=monthly_spending,
            category_breakdown=category_breakdown,
            budgets=budgets,
            recent_transactions=recent_transactions,
            nudges=nudges
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error fetching dashboard for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching dashboard"
        )


@router.get("/reports/weekly", response_model=WeeklyReportResponse, status_code=status.HTTP_200_OK)
async def get_weekly_report(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
) -> WeeklyReportResponse:
    """
    Get weekly spending report.
    
    Provides weekly financial summary including:
    - Total spent and earned
    - Net change
    - Top spending categories
    - Comparison to previous week
    - Transaction count
    
    Args:
        current_user: Authenticated user info (injected)
        db: Database instance (injected)
    
    Returns:
        Weekly report data
    
    Example:
        GET /api/v1/reports/weekly
        Headers: Authorization: Bearer <token>
        
        Response:
        {
            "week_start": "2025-01-13T00:00:00Z",
            "week_end": "2025-01-19T23:59:59Z",
            "total_spent": 3500.0,
            "total_earned": 8000.0,
            "net_change": 4500.0,
            "top_categories": [...],
            "comparison_to_previous_week": {...},
            "transaction_count": 45
        }
    """
    user_id = current_user["user_id"]
    
    logger.info(f"Generating weekly report for user {user_id}")
    
    try:
        # Calculate current week date range (Monday to Sunday)
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())  # Monday
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        week_start_str = week_start.isoformat() + "Z"
        week_end_str = week_end.isoformat() + "Z"
        
        # Get current week transactions
        current_week_txns = await get_transactions(
            db,
            user_id=user_id,
            start_date=week_start_str,
            end_date=week_end_str
        )
        
        logger.debug(f"Retrieved {len(current_week_txns)} transactions for current week")
        
        # Calculate totals
        total_spent = sum(
            t.get("amount", 0) for t in current_week_txns
            if t.get("transaction_type") == "debit"
        )
        total_earned = sum(
            t.get("amount", 0) for t in current_week_txns
            if t.get("transaction_type") == "credit"
        )
        net_change = total_earned - total_spent
        
        # Get category breakdown
        debit_txns = [t for t in current_week_txns if t.get("transaction_type") == "debit"]
        summary = summarize_transactions(debit_txns)
        
        # Top categories (sorted by amount)
        category_amounts = {
            k: v for k, v in summary.items()
            if k not in ["total", "transaction_count"] and v > 0
        }
        top_categories = [
            {"category": cat, "amount": amt}
            for cat, amt in sorted(category_amounts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Get previous week for comparison
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_start - timedelta(seconds=1)
        
        prev_week_start_str = prev_week_start.isoformat() + "Z"
        prev_week_end_str = prev_week_end.isoformat() + "Z"
        
        prev_week_txns = await get_transactions(
            db,
            user_id=user_id,
            start_date=prev_week_start_str,
            end_date=prev_week_end_str
        )
        
        prev_total_spent = sum(
            t.get("amount", 0) for t in prev_week_txns
            if t.get("transaction_type") == "debit"
        )
        
        # Calculate comparison
        if prev_total_spent > 0:
            spending_change = total_spent - prev_total_spent
            spending_change_percentage = (spending_change / prev_total_spent) * 100
        else:
            spending_change = total_spent
            spending_change_percentage = 100.0 if total_spent > 0 else 0.0
        
        comparison = {
            "previous_week_spending": prev_total_spent,
            "spending_change": spending_change,
            "spending_change_percentage": round(spending_change_percentage, 1),
            "trend": "up" if spending_change > 0 else "down" if spending_change < 0 else "stable"
        }
        
        logger.info(f"Weekly report generated for user {user_id}: "
                   f"spent={total_spent}, earned={total_earned}, "
                   f"change={spending_change_percentage:.1f}%")
        
        return WeeklyReportResponse(
            week_start=week_start_str,
            week_end=week_end_str,
            total_spent=total_spent,
            total_earned=total_earned,
            net_change=net_change,
            top_categories=top_categories,
            comparison_to_previous_week=comparison,
            transaction_count=len(current_week_txns)
        )
    
    except Exception as e:
        logger.error(f"Error generating weekly report for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while generating weekly report"
        )


@router.get("/reports/monthly", response_model=MonthlyReportResponse, status_code=status.HTTP_200_OK)
async def get_monthly_report(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db)
) -> MonthlyReportResponse:
    """
    Get monthly spending report.
    
    Provides comprehensive monthly financial summary including:
    - Total spent and earned
    - Net change
    - Category trends
    - Budget adherence
    - Daily average spending
    - Gig worker specific insights
    - Transaction count
    
    Args:
        current_user: Authenticated user info (injected)
        db: Database instance (injected)
    
    Returns:
        Monthly report data with gig worker insights
    
    Example:
        GET /api/v1/reports/monthly
        Headers: Authorization: Bearer <token>
        
        Response:
        {
            "month": "January",
            "year": 2025,
            "total_spent": 22000.0,
            "total_earned": 31500.0,
            "net_change": 9500.0,
            "category_trends": {...},
            "budget_adherence": [...],
            "daily_average": 733.33,
            "transaction_count": 120,
            "gig_worker_insights": {...}
        }
    """
    user_id = current_user["user_id"]
    phone = current_user["phone"]
    
    logger.info(f"Generating monthly report for user {user_id}")
    
    try:
        # Get user profile
        user = await get_user_by_phone(db, phone)
        
        if not user:
            logger.warning(f"User profile not found for user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Calculate current month date range
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start_str = month_start.isoformat() + "Z"
        month_end_str = now.isoformat() + "Z"
        
        # Get current month transactions
        transactions = await get_transactions(
            db,
            user_id=user_id,
            start_date=month_start_str,
            end_date=month_end_str
        )
        
        logger.debug(f"Retrieved {len(transactions)} transactions for current month")
        
        # Calculate totals
        total_spent = sum(
            t.get("amount", 0) for t in transactions
            if t.get("transaction_type") == "debit"
        )
        total_earned = sum(
            t.get("amount", 0) for t in transactions
            if t.get("transaction_type") == "credit"
        )
        net_change = total_earned - total_spent
        
        # Get category trends
        debit_txns = [t for t in transactions if t.get("transaction_type") == "debit"]
        summary = summarize_transactions(debit_txns)
        
        category_trends = {
            k: v for k, v in summary.items()
            if k not in ["total", "transaction_count"] and v > 0
        }
        
        # Calculate budget adherence
        budgets = user.get("budgets", [])
        budget_adherence = []
        
        for budget in budgets:
            category = budget.get("category")
            monthly_limit = budget.get("monthly_limit", 0.0)
            current_spent = category_trends.get(category, 0.0)
            
            if monthly_limit > 0:
                adherence_percentage = (current_spent / monthly_limit) * 100
                status = "over" if current_spent > monthly_limit else "under" if current_spent < monthly_limit * 0.9 else "on_track"
            else:
                adherence_percentage = 0.0
                status = "no_limit"
            
            budget_adherence.append({
                "category": category,
                "monthly_limit": monthly_limit,
                "current_spent": current_spent,
                "remaining": max(0, monthly_limit - current_spent),
                "adherence_percentage": round(adherence_percentage, 1),
                "status": status
            })
        
        # Calculate daily average
        days_in_month = now.day
        daily_average = total_spent / days_in_month if days_in_month > 0 else 0.0
        
        # Generate gig worker insights
        gig_worker_insights = generate_gig_worker_insights(user, transactions)
        
        # Month name
        month_name = now.strftime("%B")
        year = now.year
        
        logger.info(f"Monthly report generated for user {user_id}: "
                   f"spent={total_spent}, earned={total_earned}, "
                   f"net={net_change}, daily_avg={daily_average:.2f}")
        
        return MonthlyReportResponse(
            month=month_name,
            year=year,
            total_spent=total_spent,
            total_earned=total_earned,
            net_change=net_change,
            category_trends=category_trends,
            budget_adherence=budget_adherence,
            daily_average=round(daily_average, 2),
            transaction_count=len(transactions),
            gig_worker_insights=gig_worker_insights
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error generating monthly report for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while generating monthly report"
        )
