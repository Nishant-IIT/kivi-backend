"""
Nudge Engine Service

Purpose:
    Generate rule-based financial nudges and insights for gig workers.
    Evaluates spending patterns, income volatility, and financial goals to provide
    personalized notifications and recommendations.

Dependencies:
    - app.models.transaction_model: Transaction data access
    - app.db.mongodb: Database access layer

Usage:
    from app.services.nudge_engine import generate_nudges, generate_gig_worker_insights, evaluate_rules
    
    # Generate nudges for user
    nudges = generate_nudges(user, transactions)
    # Returns: ["Low balance alert: ₹4,500 remaining", "Food budget exceeded by ₹200"]
    
    # Generate gig worker insights
    insights = generate_gig_worker_insights(user, transactions)
    # Returns: {"best_earning_day": "Saturday", "top_platform": "Swiggy", ...}
    
    # Evaluate rules after transaction
    await evaluate_rules(db, user_id, transaction)

Reference:
    Requirements: 9.4, 9.5, 21.1, 21.2, 21.3, 21.4, 21.5
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger("kivi")


def generate_nudges(user: Dict[str, Any], transactions: List[Dict[str, Any]]) -> List[str]:
    """
    Generate rule-based financial nudges for gig workers.
    
    Checks for:
    - Low balance (critical for gig workers with irregular income)
    - Budget exceeded in any category
    - Unusual spending patterns
    - Savings goal progress
    - Income volatility warnings
    - Emergency fund adequacy
    
    Args:
        user: User profile dictionary with financial_summary, budgets, goals, notification_preferences
        transactions: List of recent transaction dictionaries
    
    Returns:
        List of nudge message strings
    
    Example:
        user = {
            "financial_summary": {"current_balance": 4500, ...},
            "budgets": [{"category": "food", "monthly_limit": 5000, "current_spent": 5200}],
            "goals": [{"name": "Emergency Fund", "target_amount": 30000, "current_amount": 12000}],
            "notification_preferences": {"low_balance_threshold": 5000}
        }
        nudges = generate_nudges(user, transactions)
        # Returns: ["Low balance alert: ₹4,500 remaining", "Food budget exceeded by ₹200"]
    """
    nudges = []
    
    # Get user preferences and financial data
    prefs = user.get("notification_preferences", {})
    financial_summary = user.get("financial_summary", {})
    budgets = user.get("budgets", [])
    goals = user.get("goals", [])
    
    current_balance = financial_summary.get("current_balance", 0.0)
    low_balance_threshold = prefs.get("low_balance_threshold", 5000.0)
    monthly_expenses = financial_summary.get("monthly_expenses", 0.0)
    income_volatility = financial_summary.get("income_volatility", "medium")
    
    # 1. Low Balance Alert (critical for gig workers)
    if current_balance < low_balance_threshold:
        nudges.append(
            f"⚠️ Low balance alert: ₹{current_balance:,.2f} remaining. "
            f"Consider taking more orders or reducing non-essential expenses."
        )
    
    # 2. Critical Low Balance (less than 3 days of expenses)
    if monthly_expenses > 0:
        daily_expenses = monthly_expenses / 30
        days_of_runway = current_balance / daily_expenses if daily_expenses > 0 else 999
        
        if days_of_runway < 3:
            nudges.append(
                f"🚨 Critical: Your balance covers only {days_of_runway:.1f} days of expenses. "
                f"Prioritize earning activities immediately."
            )
    
    # 3. Budget Exceeded Alerts
    for budget in budgets:
        category = budget.get("category", "unknown")
        monthly_limit = budget.get("monthly_limit", 0.0)
        current_spent = budget.get("current_spent", 0.0)
        
        if current_spent > monthly_limit:
            overage = current_spent - monthly_limit
            overage_percentage = (overage / monthly_limit) * 100
            
            nudges.append(
                f"💸 {category.capitalize()} budget exceeded by ₹{overage:,.2f} "
                f"({overage_percentage:.1f}% over limit)."
            )
        elif current_spent > (monthly_limit * 0.9):
            # Warning when approaching limit
            remaining = monthly_limit - current_spent
            nudges.append(
                f"⚡ {category.capitalize()} budget: ₹{remaining:,.2f} remaining "
                f"({(current_spent/monthly_limit)*100:.1f}% used)."
            )
    
    # 4. Unusual Spending Detection
    if len(transactions) > 0:
        # Calculate average transaction amount
        debit_transactions = [t for t in transactions if t.get("transaction_type") == "debit"]
        
        if len(debit_transactions) > 5:
            avg_amount = sum(t.get("amount", 0) for t in debit_transactions) / len(debit_transactions)
            
            # Check for unusually large transactions (3x average)
            for txn in debit_transactions[:5]:  # Check recent 5 transactions
                amount = txn.get("amount", 0)
                if amount > (avg_amount * 3):
                    vendor = txn.get("vendor", "Unknown")
                    nudges.append(
                        f"🔍 Unusual spending detected: ₹{amount:,.2f} at {vendor} "
                        f"(3x your average transaction)."
                    )
                    break  # Only alert once
    
    # 5. Savings Goal Progress
    for goal in goals:
        goal_name = goal.get("name", "Savings Goal")
        target_amount = goal.get("target_amount", 0.0)
        current_amount = goal.get("current_amount", 0.0)
        deadline = goal.get("deadline")
        priority = goal.get("priority", "medium")
        
        if target_amount > 0:
            progress_percentage = (current_amount / target_amount) * 100
            
            # Milestone alerts (25%, 50%, 75%, 100%)
            if 24 <= progress_percentage < 26:
                nudges.append(
                    f"🎯 {goal_name}: 25% complete! ₹{current_amount:,.2f} of ₹{target_amount:,.2f}."
                )
            elif 49 <= progress_percentage < 51:
                nudges.append(
                    f"🎯 {goal_name}: Halfway there! ₹{current_amount:,.2f} of ₹{target_amount:,.2f}."
                )
            elif 74 <= progress_percentage < 76:
                nudges.append(
                    f"🎯 {goal_name}: 75% complete! Almost there - ₹{target_amount - current_amount:,.2f} to go."
                )
            elif progress_percentage >= 100:
                nudges.append(
                    f"🎉 Congratulations! You've achieved your {goal_name} goal!"
                )
            
            # Deadline warnings for high priority goals
            if priority == "high" and deadline:
                try:
                    deadline_date = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                    days_remaining = (deadline_date - datetime.now()).days
                    
                    if 0 < days_remaining <= 30 and progress_percentage < 80:
                        required_monthly = (target_amount - current_amount)
                        nudges.append(
                            f"⏰ {goal_name} deadline in {days_remaining} days. "
                            f"Need to save ₹{required_monthly:,.2f} to reach target."
                        )
                except (ValueError, TypeError):
                    pass  # Invalid deadline format
    
    # 6. Income Volatility Warnings (gig worker specific)
    if income_volatility == "high":
        last_30_days_income = financial_summary.get("last_30_days_income", 0.0)
        avg_monthly_income = financial_summary.get("avg_monthly_income", 0.0)
        
        if avg_monthly_income > 0 and last_30_days_income < (avg_monthly_income * 0.7):
            income_drop = ((avg_monthly_income - last_30_days_income) / avg_monthly_income) * 100
            nudges.append(
                f"📉 Income alert: Your last 30 days income is {income_drop:.1f}% below average. "
                f"Consider diversifying income sources or increasing work hours."
            )
    
    # 7. Emergency Fund Adequacy (critical for gig workers)
    emergency_fund_goal = next(
        (g for g in goals if "emergency" in g.get("name", "").lower()),
        None
    )
    
    if emergency_fund_goal and monthly_expenses > 0:
        current_fund = emergency_fund_goal.get("current_amount", 0.0)
        months_covered = current_fund / monthly_expenses if monthly_expenses > 0 else 0
        
        if months_covered < 1:
            nudges.append(
                f"🛡️ Emergency fund covers only {months_covered:.1f} months of expenses. "
                f"Aim for at least 3 months for income stability."
            )
        elif months_covered >= 3:
            nudges.append(
                f"✅ Great job! Your emergency fund covers {months_covered:.1f} months of expenses."
            )
    
    # 8. Income Diversification Suggestion
    income_sources = financial_summary.get("income_sources", {})
    if len(income_sources) > 0:
        total_income = sum(income_sources.values())
        
        # Check if one platform dominates (>70% of income)
        for platform, amount in income_sources.items():
            if total_income > 0 and (amount / total_income) > 0.7:
                percentage = (amount / total_income) * 100
                nudges.append(
                    f"💡 {percentage:.1f}% of your income is from {platform}. "
                    f"Consider diversifying across platforms to reduce risk."
                )
                break
    
    logger.info(f"Generated {len(nudges)} nudges for user")
    return nudges


def generate_gig_worker_insights(user: Dict[str, Any], transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate insights specific to gig workers.
    
    Analyzes:
    - Income patterns (best earning days/hours)
    - Platform comparison (which platform pays better)
    - Expense optimization for gig work (fuel, maintenance)
    - Emergency fund runway (months of expenses covered)
    - Work-life balance indicators
    
    Args:
        user: User profile dictionary with gig_platforms and financial_summary
        transactions: List of transaction dictionaries including income (credits) and expenses (debits)
    
    Returns:
        Dictionary with gig worker insights:
        {
            "best_earning_day": "Saturday",
            "best_earning_hours": "18:00-21:00",
            "top_platform": "Swiggy",
            "top_platform_earnings": 18000.0,
            "platform_comparison": {"Swiggy": 18000, "Zomato": 10500, "Dunzo": 3000},
            "avg_earnings_per_platform": {"Swiggy": 450, "Zomato": 350, "Dunzo": 300},
            "gig_work_expenses": 2300.0,
            "gig_expense_breakdown": {"fuel": 1500, "bike_maintenance": 500, "platform_fees": 300},
            "net_gig_income": 29200.0,
            "emergency_fund_months": 1.5,
            "work_intensity": "high",
            "recommendations": [...]
        }
    """
    insights = {}
    recommendations = []
    
    financial_summary = user.get("financial_summary", {})
    gig_platforms = user.get("gig_platforms", [])
    income_sources = financial_summary.get("income_sources", {})
    monthly_expenses = financial_summary.get("monthly_expenses", 0.0)
    goals = user.get("goals", [])
    
    # 1. Platform Comparison
    if income_sources:
        insights["platform_comparison"] = income_sources
        
        # Find top earning platform
        top_platform = max(income_sources, key=income_sources.get)
        top_platform_earnings = income_sources[top_platform]
        
        insights["top_platform"] = top_platform
        insights["top_platform_earnings"] = top_platform_earnings
        
        # Calculate total income
        total_income = sum(income_sources.values())
        insights["total_platform_income"] = total_income
        
        # Platform performance comparison
        if len(income_sources) > 1:
            platform_percentages = {
                platform: (amount / total_income) * 100
                for platform, amount in income_sources.items()
            }
            insights["platform_income_distribution"] = platform_percentages
            
            # Recommendation for platform optimization
            if platform_percentages[top_platform] > 70:
                recommendations.append(
                    f"{top_platform} provides {platform_percentages[top_platform]:.1f}% of your income. "
                    f"Consider balancing across platforms for stability."
                )
            else:
                recommendations.append(
                    f"Good diversification! Income spread across {len(income_sources)} platforms."
                )
    
    # 2. Income Pattern Analysis (from transactions)
    credit_transactions = [t for t in transactions if t.get("transaction_type") == "credit"]
    
    if credit_transactions:
        # Analyze by day of week
        day_earnings = defaultdict(float)
        day_counts = defaultdict(int)
        
        for txn in credit_transactions:
            timestamp = txn.get("timestamp", "")
            amount = txn.get("amount", 0.0)
            
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                day_name = dt.strftime("%A")
                day_earnings[day_name] += amount
                day_counts[day_name] += 1
            except (ValueError, TypeError):
                continue
        
        if day_earnings:
            best_day = max(day_earnings, key=day_earnings.get)
            insights["best_earning_day"] = best_day
            insights["best_day_earnings"] = day_earnings[best_day]
            insights["daily_earnings_breakdown"] = dict(day_earnings)
            
            recommendations.append(
                f"Your best earning day is {best_day} with ₹{day_earnings[best_day]:,.2f}. "
                f"Consider working more on this day."
            )
        
        # Analyze by hour (peak earning hours)
        hour_earnings = defaultdict(float)
        
        for txn in credit_transactions:
            timestamp = txn.get("timestamp", "")
            amount = txn.get("amount", 0.0)
            
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                hour = dt.hour
                hour_earnings[hour] += amount
            except (ValueError, TypeError):
                continue
        
        if hour_earnings:
            best_hour = max(hour_earnings, key=hour_earnings.get)
            
            # Convert to time range
            if 6 <= best_hour < 12:
                best_time_range = "Morning (6AM-12PM)"
            elif 12 <= best_hour < 18:
                best_time_range = "Afternoon (12PM-6PM)"
            elif 18 <= best_hour < 24:
                best_time_range = "Evening (6PM-12AM)"
            else:
                best_time_range = "Night (12AM-6AM)"
            
            insights["best_earning_hours"] = best_time_range
            insights["peak_hour"] = best_hour
            
            recommendations.append(
                f"Peak earning hours: {best_time_range}. Focus your work during these times."
            )
        
        # Average earnings per transaction
        avg_per_transaction = sum(t.get("amount", 0) for t in credit_transactions) / len(credit_transactions)
        insights["avg_earnings_per_transaction"] = round(avg_per_transaction, 2)
    
    # 3. Gig Work Expense Analysis
    debit_transactions = [t for t in transactions if t.get("transaction_type") == "debit"]
    
    gig_expense_categories = ["fuel", "bike_maintenance", "platform_fees"]
    gig_expense_breakdown = {}
    total_gig_expenses = 0.0
    
    for category in gig_expense_categories:
        category_expenses = sum(
            t.get("amount", 0) for t in debit_transactions
            if t.get("category") == category
        )
        gig_expense_breakdown[category] = category_expenses
        total_gig_expenses += category_expenses
    
    insights["gig_work_expenses"] = total_gig_expenses
    insights["gig_expense_breakdown"] = gig_expense_breakdown
    
    # Calculate net gig income (income - gig expenses)
    total_income = sum(income_sources.values()) if income_sources else 0.0
    net_gig_income = total_income - total_gig_expenses
    insights["net_gig_income"] = net_gig_income
    
    if total_income > 0:
        expense_ratio = (total_gig_expenses / total_income) * 100
        insights["gig_expense_ratio"] = round(expense_ratio, 1)
        
        if expense_ratio > 20:
            recommendations.append(
                f"Gig work expenses are {expense_ratio:.1f}% of income. "
                f"Look for ways to optimize fuel and maintenance costs."
            )
        else:
            recommendations.append(
                f"Good expense management! Gig expenses are only {expense_ratio:.1f}% of income."
            )
    
    # 4. Emergency Fund Runway
    emergency_fund_goal = next(
        (g for g in goals if "emergency" in g.get("name", "").lower()),
        None
    )
    
    if emergency_fund_goal and monthly_expenses > 0:
        current_fund = emergency_fund_goal.get("current_amount", 0.0)
        months_covered = current_fund / monthly_expenses
        insights["emergency_fund_months"] = round(months_covered, 1)
        
        if months_covered < 3:
            recommendations.append(
                f"Emergency fund covers {months_covered:.1f} months. "
                f"Aim for 3-6 months for gig work stability."
            )
    else:
        insights["emergency_fund_months"] = 0.0
        recommendations.append(
            "Consider creating an emergency fund to handle income fluctuations."
        )
    
    # 5. Work Intensity Analysis
    if credit_transactions:
        # Calculate transactions per day
        days_with_income = len(set(
            datetime.fromisoformat(t.get("timestamp", "").replace("Z", "+00:00")).date()
            for t in credit_transactions
            if t.get("timestamp")
        ))
        
        if days_with_income > 0:
            avg_transactions_per_day = len(credit_transactions) / days_with_income
            
            if avg_transactions_per_day > 15:
                work_intensity = "very_high"
                intensity_label = "Very High"
            elif avg_transactions_per_day > 10:
                work_intensity = "high"
                intensity_label = "High"
            elif avg_transactions_per_day > 5:
                work_intensity = "medium"
                intensity_label = "Medium"
            else:
                work_intensity = "low"
                intensity_label = "Low"
            
            insights["work_intensity"] = work_intensity
            insights["avg_orders_per_day"] = round(avg_transactions_per_day, 1)
            
            if work_intensity in ["very_high", "high"]:
                recommendations.append(
                    f"Work intensity is {intensity_label} ({avg_transactions_per_day:.1f} orders/day). "
                    f"Remember to take breaks and maintain work-life balance."
                )
    
    # 6. Platform-Specific Recommendations
    if income_sources and len(income_sources) > 1:
        # Calculate average per platform
        avg_per_platform = {}
        
        for platform in income_sources:
            platform_transactions = [
                t for t in credit_transactions
                if platform.lower() in t.get("vendor", "").lower()
            ]
            
            if platform_transactions:
                avg_per_platform[platform] = income_sources[platform] / len(platform_transactions)
        
        if avg_per_platform:
            insights["avg_earnings_per_platform"] = avg_per_platform
            
            best_avg_platform = max(avg_per_platform, key=avg_per_platform.get)
            worst_avg_platform = min(avg_per_platform, key=avg_per_platform.get)
            
            if avg_per_platform[best_avg_platform] > avg_per_platform[worst_avg_platform] * 1.5:
                recommendations.append(
                    f"{best_avg_platform} has {avg_per_platform[best_avg_platform]:.0f}% higher "
                    f"average earnings per order than {worst_avg_platform}. "
                    f"Consider prioritizing {best_avg_platform} orders."
                )
    
    insights["recommendations"] = recommendations
    
    logger.info(f"Generated gig worker insights with {len(recommendations)} recommendations")
    return insights


async def evaluate_rules(db: Any, user_id: str, transaction: Dict[str, Any]) -> None:
    """
    Evaluate user rules and trigger notifications.
    
    Checks active rules for the user against the new transaction and creates
    notification records when rule conditions are met. Sends WhatsApp messages
    for triggered rules.
    
    Rule types supported:
    - budget_exceeded: Alert when category spending exceeds budget
    - low_balance: Alert when balance falls below threshold
    - unusual_spending: Alert for transactions significantly above average
    - savings_goal_progress: Alert on goal milestones
    
    Args:
        db: Database instance (MockDatabase or AsyncIOMotorDatabase)
        user_id: User identifier
        transaction: Transaction dictionary that triggered evaluation
    
    Example:
        # After creating a transaction
        await evaluate_rules(db, "usr_1234567890", {
            "transaction_id": "txn_001",
            "user_id": "usr_1234567890",
            "amount": 500.0,
            "category": "food",
            "transaction_type": "debit"
        })
    """
    try:
        logger.debug(f"Evaluating rules for user {user_id} after transaction {transaction.get('transaction_id')}")
        
        # Get active rules for user
        rules = await db.user_rules.find({"user_id": user_id, "active": True})
        
        if not rules:
            logger.debug(f"No active rules found for user {user_id}")
            return
        
        # Get user profile for context
        from app.models.user_model import get_user_by_phone
        user = await db.users.find_one({"user_id": user_id})
        
        if not user:
            logger.warning(f"User {user_id} not found for rule evaluation")
            return
        
        # Evaluate each rule
        for rule in rules:
            rule_id = rule.get("rule_id", "unknown")
            rule_type = rule.get("rule_type", "")
            conditions = rule.get("conditions", {})
            threshold_values = rule.get("threshold_values", {})
            
            logger.debug(f"Evaluating rule {rule_id} (type: {rule_type})")
            
            notification_message = None
            
            # Budget Exceeded Rule
            if rule_type == "budget_exceeded":
                category = conditions.get("category")
                threshold_percentage = conditions.get("threshold_percentage", 100)
                
                if transaction.get("category") == category:
                    # Get budget for category
                    budgets = user.get("budgets", [])
                    budget = next((b for b in budgets if b.get("category") == category), None)
                    
                    if budget:
                        monthly_limit = budget.get("monthly_limit", 0.0)
                        current_spent = budget.get("current_spent", 0.0)
                        
                        # Check if threshold exceeded
                        if monthly_limit > 0:
                            spent_percentage = (current_spent / monthly_limit) * 100
                            
                            if spent_percentage >= threshold_percentage:
                                overage = current_spent - monthly_limit
                                notification_message = (
                                    f"Budget Alert: You've exceeded your {category} budget "
                                    f"by ₹{overage:,.2f} ({spent_percentage:.1f}% of limit)."
                                )
            
            # Low Balance Rule
            elif rule_type == "low_balance":
                threshold = threshold_values.get("balance_threshold", 5000.0)
                
                financial_summary = user.get("financial_summary", {})
                current_balance = financial_summary.get("current_balance", 0.0)
                
                if current_balance < threshold:
                    notification_message = (
                        f"Low Balance Alert: Your balance is ₹{current_balance:,.2f}, "
                        f"below your threshold of ₹{threshold:,.2f}."
                    )
            
            # Unusual Spending Rule
            elif rule_type == "unusual_spending":
                multiplier = threshold_values.get("multiplier", 3.0)
                
                # Get recent transactions to calculate average
                from app.models.transaction_model import get_transactions
                recent_txns = await get_transactions(db, user_id)
                
                debit_txns = [t for t in recent_txns if t.get("transaction_type") == "debit"]
                
                if len(debit_txns) > 5:
                    avg_amount = sum(t.get("amount", 0) for t in debit_txns) / len(debit_txns)
                    
                    if transaction.get("amount", 0) > (avg_amount * multiplier):
                        notification_message = (
                            f"Unusual Spending: ₹{transaction.get('amount', 0):,.2f} at "
                            f"{transaction.get('vendor', 'Unknown')} is {multiplier}x your average transaction."
                        )
            
            # Savings Goal Progress Rule
            elif rule_type == "savings_goal_progress":
                goal_id = conditions.get("goal_id")
                milestone_percentage = conditions.get("milestone_percentage", 50)
                
                goals = user.get("goals", [])
                goal = next((g for g in goals if g.get("goal_id") == goal_id), None)
                
                if goal:
                    target_amount = goal.get("target_amount", 0.0)
                    current_amount = goal.get("current_amount", 0.0)
                    
                    if target_amount > 0:
                        progress_percentage = (current_amount / target_amount) * 100
                        
                        # Check if milestone reached (with 2% tolerance)
                        if abs(progress_percentage - milestone_percentage) < 2:
                            notification_message = (
                                f"Goal Milestone: {goal.get('name')} is {milestone_percentage}% complete! "
                                f"₹{current_amount:,.2f} of ₹{target_amount:,.2f}."
                            )
            
            # Create notification if rule triggered
            if notification_message:
                notification = {
                    "notification_id": f"notif_{user_id[-10:]}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                    "user_id": user_id,
                    "trigger_type": rule_type,
                    "rule_id": rule_id,
                    "message": notification_message,
                    "status": "pending",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "metadata": {
                        "transaction_id": transaction.get("transaction_id"),
                        "amount": transaction.get("amount"),
                        "category": transaction.get("category")
                    }
                }
                
                # Save notification
                await db.notifications.insert_one(notification)
                logger.info(f"Created notification {notification['notification_id']} for rule {rule_id}")
                
                # TODO: Send WhatsApp message via whatsapp_service.send_whatsapp_text()
                # This will be implemented when WhatsApp service is available
                # For now, just log the notification
                logger.info(f"Notification to send: {notification_message}")
        
        logger.info(f"Completed rule evaluation for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error evaluating rules for user {user_id}: {e}", exc_info=True)
