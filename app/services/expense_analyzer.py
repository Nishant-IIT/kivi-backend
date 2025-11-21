"""
Expense Analyzer Service

Purpose:
    Categorize transactions and provide spending summaries.
    Includes gig-worker specific categories for delivery partners, ride-share drivers, etc.

Dependencies:
    - None (pure Python functions)

Example Usage:
    from app.services.expense_analyzer import categorize_transaction, summarize_transactions
    
    txn = {
        "amount": 450.0,
        "vendor": "Swiggy",
        "category": None
    }
    category = categorize_transaction(txn)
    # Returns: "food"
    
    transactions = [
        {"amount": 450.0, "category": "food"},
        {"amount": 200.0, "category": "transport"}
    ]
    summary = summarize_transactions(transactions)
    # Returns: {"food": 450.0, "transport": 200.0, "total": 650.0}
"""

from typing import Dict, List, Optional


# Category keyword mappings
# Note: Order matters - more specific categories should come first
CATEGORY_KEYWORDS = {
    "fuel": [
        # Gig-worker specific: Fuel expenses
        "petrol", "diesel", "fuel", "gas station", "cng", "bharat petroleum", "bpcl",
        "indian oil", "iocl", "hp petrol", "hp diesel", "hindustan petroleum", "hpcl", "shell",
        "reliance petroleum", "essar", "nayara"
    ],
    
    "bike_maintenance": [
        # Gig-worker specific: Vehicle maintenance
        "bike", "motorcycle", "scooter", "two wheeler", "service center", "repair",
        "mechanic", "spare parts", "tyre", "tire", "oil change", "battery",
        "puncture", "garage", "workshop", "servicing"
    ],
    
    "platform_fees": [
        # Gig-worker specific: Platform commissions and fees
        "swiggy commission", "zomato commission", "uber commission", "ola commission",
        "platform fee", "service charge", "commission", "subscription fee",
        "swiggy pro", "zomato gold", "uber pass", "ola money"
    ],
    
    "food": [
        # Restaurants and food delivery
        "swiggy", "zomato", "uber eats", "ubereats", "dominos", "domino's", "pizza",
        "mcdonald", "mcdonalds", "kfc", "burger king", "subway", "starbucks",
        "restaurant", "cafe", "coffee", "food", "meal", "lunch", "dinner", "breakfast",
        "biryani", "chinese", "cuisine", "eatery", "diner", "bakery",
        # Grocery and food stores
        "bigbasket", "grofers", "blinkit", "dunzo", "grocery", "supermarket",
        "dmart", "reliance fresh", "more", "spencer", "food bazaar"
    ],
    
    "transport": [
        # Ride-sharing and taxis
        "uber", "ola", "rapido", "meru", "taxi", "cab", "auto", "rickshaw",
        # Public transport
        "metro", "bus", "train", "railway", "irctc", "redbus", "paytm bus",
        # Parking and tolls
        "parking", "toll", "fastag", "toll plaza"
    ],
    
    "bike_maintenance": [
        # Gig-worker specific: Vehicle maintenance
        "bike", "motorcycle", "scooter", "two wheeler", "service", "repair",
        "mechanic", "spare parts", "tyre", "tire", "oil change", "battery",
        "puncture", "garage", "workshop", "servicing"
    ],
    
    "platform_fees": [
        # Gig-worker specific: Platform commissions and fees
        "swiggy commission", "zomato commission", "uber commission", "ola commission",
        "platform fee", "service charge", "commission", "subscription fee",
        "swiggy pro", "zomato gold", "uber pass", "ola money"
    ],
    
    "shopping": [
        # E-commerce
        "amazon", "flipkart", "myntra", "ajio", "meesho", "snapdeal",
        # Retail stores
        "shopping", "mall", "store", "retail", "purchase", "buy",
        # Specific categories
        "clothing", "electronics", "mobile", "phone", "laptop", "accessories"
    ],
    
    "bills": [
        # Utilities
        "electricity", "water", "gas bill", "lpg", "cylinder",
        # Telecom
        "airtel", "jio", "vodafone", "vi", "bsnl", "mobile recharge", "recharge",
        "broadband", "internet", "wifi",
        # Other bills
        "bill payment", "utility", "rent", "emi", "loan", "insurance"
    ],
    
    "entertainment": [
        # Streaming services
        "netflix", "amazon prime", "hotstar", "disney", "zee5", "sony liv",
        # Movies and events
        "movie", "cinema", "pvr", "inox", "bookmyshow", "paytm insider",
        # Gaming and hobbies
        "game", "gaming", "playstation", "xbox", "steam"
    ],
    
    "healthcare": [
        # Medical services
        "hospital", "clinic", "doctor", "medical", "pharmacy", "medicine",
        "apollo", "fortis", "max healthcare", "medanta",
        # Online pharmacies
        "1mg", "pharmeasy", "netmeds", "apollo pharmacy",
        # Health services
        "lab test", "diagnostic", "health checkup", "consultation"
    ],
    
    "education": [
        # Educational platforms
        "udemy", "coursera", "unacademy", "byju", "byjus", "vedantu",
        # Books and learning
        "book", "course", "training", "tuition", "coaching", "class",
        "education", "learning", "study", "school", "college", "university"
    ]
}


def categorize_transaction(txn: dict) -> str:
    """
    Classify transaction into a category using keyword matching.
    
    Categories include:
    - Standard: food, transport, shopping, bills, entertainment, healthcare, education
    - Gig-worker specific: fuel, bike_maintenance, platform_fees
    - Default: others
    
    Args:
        txn: Transaction dictionary with at least "vendor" field
    
    Returns:
        Category string (e.g., "food", "transport", "fuel", "others")
    """
    # If category already exists, return it
    if txn.get("category"):
        return txn["category"]
    
    # Get vendor name and convert to lowercase for matching
    vendor = txn.get("vendor", "").lower()
    
    # Also check raw_sms_text if available for better context
    raw_text = txn.get("raw_sms_text", "").lower()
    
    # Combine vendor and raw text for comprehensive matching
    search_text = f"{vendor} {raw_text}"
    
    # Check each category's keywords
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in search_text:
                return category
    
    # Default category if no match found
    return "others"


def summarize_transactions(transactions: List[dict]) -> dict:
    """
    Aggregate transactions by category and calculate totals.
    
    Args:
        transactions: List of transaction dictionaries with "amount" and "category" fields
    
    Returns:
        Dictionary with category totals and overall total:
        {
            "food": 1200.0,
            "transport": 800.0,
            "fuel": 1500.0,
            "bike_maintenance": 500.0,
            "platform_fees": 300.0,
            "shopping": 2000.0,
            "bills": 3000.0,
            "entertainment": 500.0,
            "healthcare": 1000.0,
            "education": 800.0,
            "others": 400.0,
            "total": 12000.0,
            "transaction_count": 25
        }
    """
    # Initialize category totals
    category_totals = {
        "food": 0.0,
        "transport": 0.0,
        "fuel": 0.0,
        "bike_maintenance": 0.0,
        "platform_fees": 0.0,
        "shopping": 0.0,
        "bills": 0.0,
        "entertainment": 0.0,
        "healthcare": 0.0,
        "education": 0.0,
        "others": 0.0
    }
    
    total_amount = 0.0
    transaction_count = 0
    
    # Process each transaction
    for txn in transactions:
        amount = txn.get("amount", 0.0)
        category = txn.get("category", "others")
        
        # Only count debit transactions for expense summary
        # (credits are income, not expenses)
        transaction_type = txn.get("transaction_type", "debit")
        if transaction_type == "debit":
            # Add to category total
            if category in category_totals:
                category_totals[category] += amount
            else:
                category_totals["others"] += amount
            
            total_amount += amount
            transaction_count += 1
    
    # Add overall totals
    category_totals["total"] = total_amount
    category_totals["transaction_count"] = transaction_count
    
    return category_totals


def get_category_insights(transactions: List[dict], user: Optional[dict] = None) -> dict:
    """
    Generate spending insights and recommendations based on transaction patterns.
    
    Provides gig-worker specific insights like:
    - High fuel costs relative to income
    - Bike maintenance frequency
    - Platform fee optimization opportunities
    
    Args:
        transactions: List of transaction dictionaries
        user: Optional user profile with income and budget information
    
    Returns:
        Dictionary with insights and recommendations:
        {
            "top_category": "food",
            "top_category_amount": 1200.0,
            "top_category_percentage": 35.5,
            "gig_work_expenses": 2300.0,  # fuel + bike_maintenance + platform_fees
            "gig_work_percentage": 19.2,
            "recommendations": [
                "Your fuel expenses are 12.5% of spending. Consider route optimization.",
                "Bike maintenance costs are high. Check for recurring issues."
            ]
        }
    """
    summary = summarize_transactions(transactions)
    
    if summary["total"] == 0:
        return {
            "top_category": None,
            "top_category_amount": 0.0,
            "top_category_percentage": 0.0,
            "gig_work_expenses": 0.0,
            "gig_work_percentage": 0.0,
            "recommendations": []
        }
    
    # Find top spending category (excluding 'others' and 'total')
    categories_only = {k: v for k, v in summary.items() 
                      if k not in ["others", "total", "transaction_count"]}
    
    top_category = max(categories_only, key=categories_only.get)
    top_category_amount = categories_only[top_category]
    top_category_percentage = (top_category_amount / summary["total"]) * 100
    
    # Calculate gig-worker specific expenses
    gig_work_expenses = (
        summary.get("fuel", 0.0) + 
        summary.get("bike_maintenance", 0.0) + 
        summary.get("platform_fees", 0.0)
    )
    gig_work_percentage = (gig_work_expenses / summary["total"]) * 100 if summary["total"] > 0 else 0.0
    
    # Generate recommendations
    recommendations = []
    
    # Fuel expense recommendations
    fuel_percentage = (summary.get("fuel", 0.0) / summary["total"]) * 100 if summary["total"] > 0 else 0.0
    if fuel_percentage > 15:
        recommendations.append(
            f"Your fuel expenses are {fuel_percentage:.1f}% of spending. Consider route optimization or carpooling."
        )
    
    # Bike maintenance recommendations
    maintenance_percentage = (summary.get("bike_maintenance", 0.0) / summary["total"]) * 100 if summary["total"] > 0 else 0.0
    if maintenance_percentage > 5:
        recommendations.append(
            f"Bike maintenance costs are {maintenance_percentage:.1f}% of expenses. Check for recurring issues."
        )
    
    # Platform fees recommendations
    platform_fee_percentage = (summary.get("platform_fees", 0.0) / summary["total"]) * 100 if summary["total"] > 0 else 0.0
    if platform_fee_percentage > 3:
        recommendations.append(
            f"Platform fees are {platform_fee_percentage:.1f}% of expenses. Compare commission rates across platforms."
        )
    
    # Food expense recommendations
    food_percentage = (summary.get("food", 0.0) / summary["total"]) * 100 if summary["total"] > 0 else 0.0
    if food_percentage > 30:
        recommendations.append(
            f"Food expenses are {food_percentage:.1f}% of spending. Consider meal planning to reduce costs."
        )
    
    # Budget comparison if user data available
    if user and user.get("budgets"):
        for budget in user["budgets"]:
            category = budget.get("category")
            limit = budget.get("monthly_limit", 0)
            spent = summary.get(category, 0.0)
            
            if spent > limit:
                overage = spent - limit
                recommendations.append(
                    f"You've exceeded your {category} budget by ₹{overage:.2f}."
                )
    
    return {
        "top_category": top_category,
        "top_category_amount": top_category_amount,
        "top_category_percentage": round(top_category_percentage, 1),
        "gig_work_expenses": gig_work_expenses,
        "gig_work_percentage": round(gig_work_percentage, 1),
        "recommendations": recommendations
    }
