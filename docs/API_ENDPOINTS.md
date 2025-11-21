# KIVI Backend API Documentation

Complete API reference for the KIVI Backend system with working curl examples.

## Table of Contents

- [Authentication](#authentication)
- [User Profile](#user-profile)
- [Finance & Transactions](#finance--transactions)
- [WhatsApp Integration](#whatsapp-integration)
- [AI Chat](#ai-chat)
- [Error Responses](#error-responses)

---

## Base URL

```
http://localhost:8000
```

For production, replace with your deployed API URL.

---

## Authentication

### POST /api/v1/login

Authenticate user and receive JWT access token.

**Request Body:**

```json
{
  "phone": "+919876543210",
  "password": "demo123"
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNyXzk4NzY1NDMyMTAiLCJwaG9uZSI6Iis5MTk4NzY1NDMyMTAiLCJleHAiOjE3MDYxMjM0NTZ9.abc123...",
  "token_type": "bearer",
  "user_id": "usr_9876543210",
  "phone": "+919876543210"
}
```

**Response (401 Unauthorized):**

```json
{
  "detail": "Invalid credentials"
}
```

**curl Example:**

```bash
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "password": "demo123"
  }'
```

**Notes:**
- For hackathon/demo: Use password `"demo123"` for any phone number
- First-time users are automatically onboarded with sample gig worker data
- Welcome WhatsApp message is sent to new users
- Token expires in 24 hours (configurable via JWT_EXPIRATION_HOURS)

---

## User Profile

All user profile endpoints require authentication via JWT token in the `Authorization` header.

### GET /api/v1/users/me

Retrieve authenticated user's complete profile.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "user_id": "usr_9876543210",
  "phone": "+919876543210",
  "name": "Rahul Sharma",
  "email": "rahul@example.com",
  "job": "Delivery Partner",
  "city": "Mumbai",
  "gig_platforms": ["Swiggy", "Zomato", "Dunzo"],
  "financial_summary": {
    "current_balance": 12000.00,
    "avg_monthly_income": 28000.00,
    "monthly_expenses": 22000.00,
    "income_volatility": "high",
    "last_30_days_income": 31500.00,
    "income_sources": {
      "Swiggy": 18000.00,
      "Zomato": 10500.00,
      "Dunzo": 3000.00
    }
  },
  "budgets": [
    {
      "category": "food",
      "monthly_limit": 5000.00,
      "current_spent": 3200.00
    },
    {
      "category": "transport",
      "monthly_limit": 3000.00,
      "current_spent": 2800.00,
      "note": "Bike fuel and maintenance"
    }
  ],
  "goals": [
    {
      "goal_id": "goal_001",
      "name": "Emergency Fund",
      "target_amount": 30000.00,
      "current_amount": 12000.00,
      "deadline": "2025-06-30",
      "priority": "high"
    }
  ],
  "notification_preferences": {
    "whatsapp_enabled": true,
    "budget_alerts": true,
    "weekly_summary": true,
    "income_tracking": true,
    "low_balance_threshold": 5000.00
  },
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-20T14:22:00Z"
}
```

**curl Example:**

```bash
# First, login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "password": "demo123"}' \
  | jq -r '.access_token')

# Then get user profile
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

---

### PUT /api/v1/users/me

Update authenticated user's profile (partial updates supported).

**Headers:**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body (all fields optional):**

```json
{
  "name": "Rahul Kumar",
  "city": "Delhi",
  "job": "Freelance Designer",
  "gig_platforms": ["Upwork", "Fiverr", "Freelancer"]
}
```

**Response (200 OK):**

```json
{
  "user_id": "usr_9876543210",
  "phone": "+919876543210",
  "name": "Rahul Kumar",
  "city": "Delhi",
  "job": "Freelance Designer",
  "gig_platforms": ["Upwork", "Fiverr", "Freelancer"],
  "financial_summary": { ... },
  "budgets": [ ... ],
  "goals": [ ... ],
  "notification_preferences": { ... },
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-21T10:15:00Z"
}
```

**curl Example:**

```bash
curl -X PUT http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rahul Kumar",
    "city": "Delhi",
    "gig_platforms": ["Uber", "Ola", "Rapido"]
  }'
```

---

## Finance & Transactions

### GET /api/v1/transactions

Retrieve transaction history with optional filters.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| start_date | string | No | Start date (ISO 8601) | 2025-01-01T00:00:00Z |
| end_date | string | No | End date (ISO 8601) | 2025-01-31T23:59:59Z |
| category | string | No | Filter by category | food |

**Response (200 OK):**

```json
[
  {
    "transaction_id": "txn_1234567890",
    "user_id": "usr_9876543210",
    "amount": 450.00,
    "vendor": "Swiggy",
    "category": "food",
    "transaction_type": "debit",
    "timestamp": "2025-01-20T19:30:00Z",
    "source": "sms",
    "raw_sms_text": "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy",
    "metadata": {
      "payment_method": "UPI"
    }
  },
  {
    "transaction_id": "txn_1234567891",
    "user_id": "usr_9876543210",
    "amount": 1200.00,
    "vendor": "Swiggy Earnings",
    "category": "income",
    "transaction_type": "credit",
    "timestamp": "2025-01-20T23:00:00Z",
    "source": "aa",
    "raw_sms_text": null,
    "metadata": {
      "platform": "Swiggy",
      "orders_completed": 15
    }
  }
]
```

**curl Examples:**

```bash
# Get all transactions
curl -X GET http://localhost:8000/api/v1/transactions \
  -H "Authorization: Bearer $TOKEN"

# Get transactions for specific date range
curl -X GET "http://localhost:8000/api/v1/transactions?start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z" \
  -H "Authorization: Bearer $TOKEN"

# Get transactions by category
curl -X GET "http://localhost:8000/api/v1/transactions?category=food" \
  -H "Authorization: Bearer $TOKEN"

# Combine filters
curl -X GET "http://localhost:8000/api/v1/transactions?start_date=2025-01-15T00:00:00Z&category=transport" \
  -H "Authorization: Bearer $TOKEN"
```

---

### POST /api/v1/transactions

Create manual transaction entry.

**Headers:**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "amount": 450.00,
  "vendor": "Swiggy",
  "category": "food",
  "transaction_type": "debit",
  "timestamp": "2025-01-20T19:30:00Z",
  "metadata": {
    "payment_method": "UPI",
    "note": "Dinner order"
  }
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| amount | float | Yes | Transaction amount |
| vendor | string | Yes | Merchant/vendor name |
| category | string | No | Category (auto-categorized if not provided) |
| transaction_type | string | Yes | "debit" or "credit" |
| timestamp | string | No | ISO 8601 timestamp (defaults to now) |
| metadata | object | No | Additional metadata |

**Response (201 Created):**

```json
{
  "transaction_id": "txn_1234567892",
  "user_id": "usr_9876543210",
  "amount": 450.00,
  "vendor": "Swiggy",
  "category": "food",
  "transaction_type": "debit",
  "timestamp": "2025-01-20T19:30:00Z",
  "source": "manual",
  "raw_sms_text": null,
  "metadata": {
    "payment_method": "UPI",
    "note": "Dinner order"
  }
}
```

**curl Example:**

```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 450.00,
    "vendor": "Swiggy",
    "transaction_type": "debit",
    "metadata": {
      "payment_method": "UPI"
    }
  }'
```

---

### POST /api/v1/transactions/sms

Parse SMS text and create transaction automatically.

**Headers:**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "sms_text": "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy"
}
```

**Response (201 Created):**

```json
{
  "transaction_id": "txn_1234567893",
  "user_id": "usr_9876543210",
  "amount": 450.00,
  "vendor": "Swiggy",
  "category": "food",
  "transaction_type": "debit",
  "timestamp": "2025-01-20T00:00:00Z",
  "source": "sms",
  "raw_sms_text": "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy",
  "metadata": {}
}
```

**curl Example:**

```bash
curl -X POST http://localhost:8000/api/v1/transactions/sms \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sms_text": "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy"
  }'
```

**Supported SMS Formats:**

The parser supports various bank SMS formats:

```
Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy
INR 1200.50 credited to A/c XX5678 from Zomato on 21-Jan-25
Your A/c XX1234 debited with Rs.350 at Shell Petrol on 22-Jan-2025
```

---

### GET /api/v1/dashboard

Get comprehensive dashboard summary.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "balance": 12000.00,
  "monthly_spending": 8500.00,
  "category_breakdown": {
    "food": 3200.00,
    "transport": 2800.00,
    "fuel": 1500.00,
    "shopping": 800.00,
    "entertainment": 200.00
  },
  "budgets": [
    {
      "category": "food",
      "monthly_limit": 5000.00,
      "current_spent": 3200.00
    },
    {
      "category": "transport",
      "monthly_limit": 3000.00,
      "current_spent": 2800.00,
      "note": "Bike fuel and maintenance"
    }
  ],
  "recent_transactions": [
    {
      "transaction_id": "txn_1234567890",
      "amount": 450.00,
      "vendor": "Swiggy",
      "category": "food",
      "transaction_type": "debit",
      "timestamp": "2025-01-20T19:30:00Z"
    }
  ],
  "nudges": [
    "You're 93% through your transport budget. Consider using public transport for the rest of the month.",
    "Great job! You're under budget on food spending this month.",
    "Your income has been lower than usual this week. Consider taking on more orders during peak hours."
  ]
}
```

**curl Example:**

```bash
curl -X GET http://localhost:8000/api/v1/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/v1/reports/weekly

Get weekly spending report with comparison to previous week.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "week_start": "2025-01-13T00:00:00Z",
  "week_end": "2025-01-19T23:59:59Z",
  "total_spent": 3500.00,
  "total_earned": 8000.00,
  "net_change": 4500.00,
  "top_categories": [
    {
      "category": "food",
      "amount": 1200.00
    },
    {
      "category": "fuel",
      "amount": 800.00
    },
    {
      "category": "transport",
      "amount": 600.00
    }
  ],
  "comparison_to_previous_week": {
    "previous_week_spending": 3200.00,
    "spending_change": 300.00,
    "spending_change_percentage": 9.4,
    "trend": "up"
  },
  "transaction_count": 45
}
```

**curl Example:**

```bash
curl -X GET http://localhost:8000/api/v1/reports/weekly \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/v1/reports/monthly

Get monthly spending report with gig worker insights.

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "month": "January",
  "year": 2025,
  "total_spent": 22000.00,
  "total_earned": 31500.00,
  "net_change": 9500.00,
  "category_trends": {
    "food": 5200.00,
    "transport": 4800.00,
    "fuel": 3500.00,
    "shopping": 2000.00,
    "bills": 3000.00,
    "entertainment": 1500.00,
    "healthcare": 1000.00,
    "others": 1000.00
  },
  "budget_adherence": [
    {
      "category": "food",
      "monthly_limit": 5000.00,
      "current_spent": 5200.00,
      "remaining": 0.00,
      "adherence_percentage": 104.0,
      "status": "over"
    },
    {
      "category": "transport",
      "monthly_limit": 3000.00,
      "current_spent": 2800.00,
      "remaining": 200.00,
      "adherence_percentage": 93.3,
      "status": "on_track"
    }
  ],
  "daily_average": 733.33,
  "transaction_count": 120,
  "gig_worker_insights": {
    "best_earning_days": ["Friday", "Saturday", "Sunday"],
    "best_earning_hours": ["12:00-14:00", "19:00-22:00"],
    "platform_comparison": {
      "Swiggy": {
        "total_earnings": 18000.00,
        "orders_completed": 180,
        "avg_per_order": 100.00
      },
      "Zomato": {
        "total_earnings": 10500.00,
        "orders_completed": 120,
        "avg_per_order": 87.50
      },
      "Dunzo": {
        "total_earnings": 3000.00,
        "orders_completed": 50,
        "avg_per_order": 60.00
      }
    },
    "emergency_fund_runway": 1.36,
    "income_volatility": "high",
    "recommendations": [
      "Focus on Swiggy orders during peak hours (12-2pm, 7-10pm) for better earnings",
      "Your emergency fund covers 1.4 months of expenses. Aim for 3-6 months.",
      "Consider diversifying income sources to reduce volatility"
    ]
  }
}
```

**curl Example:**

```bash
curl -X GET http://localhost:8000/api/v1/reports/monthly \
  -H "Authorization: Bearer $TOKEN"
```

---

## WhatsApp Integration

### POST /api/v1/whatsapp/webhook

Receive incoming WhatsApp messages from Meta Cloud API (called by Meta, not directly by users).

**Request Body (Meta Webhook Payload):**

```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "123456789",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "919876543210",
              "phone_number_id": "123456789"
            },
            "contacts": [
              {
                "profile": {
                  "name": "Rahul Sharma"
                },
                "wa_id": "919876543210"
              }
            ],
            "messages": [
              {
                "from": "919876543210",
                "id": "wamid.HBgNOTE5ODc2NTQzMjEwFQIAERgSMDhBRjE2QjdGNzY4QzQ5OTJBAA==",
                "timestamp": "1706123456",
                "text": {
                  "body": "How much did I spend on food this month?"
                },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Response (200 OK):**

```json
{
  "status": "received"
}
```

**Notes:**
- This endpoint is called by Meta's WhatsApp Cloud API
- Returns 200 OK immediately for webhook acknowledgment
- Message processing happens in background
- AI response is sent back to user via WhatsApp

---

### POST /api/v1/whatsapp/send_notification

Send proactive WhatsApp notification to user.

**Headers:**

```
Content-Type: application/json
```

**Request Body:**

```json
{
  "phone": "+919876543210",
  "text": "You've exceeded your food budget by ₹200 this month. Consider cooking at home more often!",
  "provider": "openai"
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message_id": "wamid.HBgNOTE5ODc2NTQzMjEwFQIAERgSMDhBRjE2QjdGNzY4QzQ5OTJBAA=="
}
```

**Response (500 Error):**

```json
{
  "status": "error",
  "error": "Failed to send WhatsApp message: Invalid phone number"
}
```

**curl Example:**

```bash
curl -X POST http://localhost:8000/api/v1/whatsapp/send_notification \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "text": "Your food budget is 80% spent this month.",
    "provider": "openai"
  }'
```

---

## AI Chat

### POST /api/v1/ai/chat

Send chat message from mobile app and receive AI response.

**Headers:**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "user_id": "usr_9876543210",
  "phone": "+919876543210",
  "metadata": {
    "name": "Rahul Sharma",
    "job": "Delivery Partner",
    "gig_platforms": ["Swiggy", "Zomato"],
    "transaction_summary": {
      "balance": 12000.00,
      "monthly_spending": 8500.00,
      "monthly_income": 28000.00
    }
  },
  "message": "How much did I spend on food this month?",
  "provider": "openai"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_id | string | Yes | User identifier (must match JWT token) |
| phone | string | Yes | User phone number |
| metadata | object | No | User context for personalized responses |
| message | string | Yes | User's message text |
| provider | string | No | AI provider ("openai" or "anthropic", default: "openai") |

**Response (200 OK):**

```json
{
  "reply": "Based on your transaction history, you spent ₹3,200 on food this month. That's 64% of your ₹5,000 food budget, so you're doing well! You have ₹1,800 remaining for the rest of the month.",
  "provider": "openai",
  "usage": {
    "latency_ms": 1250,
    "prompt_length": 450,
    "response_length": 185
  },
  "message_id": "msg_9876543210_20250121143022123456"
}
```

**curl Example:**

```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr_9876543210",
    "phone": "+919876543210",
    "metadata": {
      "name": "Rahul",
      "job": "Delivery Partner",
      "transaction_summary": {
        "balance": 12000.00,
        "monthly_spending": 8500.00
      }
    },
    "message": "How much did I spend on food this month?",
    "provider": "openai"
  }'
```

---

### GET /api/v1/ai/health

Health check for AI chat service.

**Response (200 OK):**

```json
{
  "status": "healthy",
  "service": "ai-chat",
  "providers": ["openai", "anthropic"]
}
```

**curl Example:**

```bash
curl -X GET http://localhost:8000/api/v1/ai/health
```

---

## Error Responses

All endpoints follow standard HTTP status codes and return errors in this format:

### 400 Bad Request

```json
{
  "detail": "Invalid SMS format: Could not extract amount from SMS text"
}
```

### 401 Unauthorized

```json
{
  "detail": "Invalid credentials"
}
```

or

```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "User ID in request does not match authenticated user"
}
```

### 404 Not Found

```json
{
  "detail": "User profile not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "amount"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error while fetching transactions"
}
```

---

## Complete Workflow Example

Here's a complete workflow showing how to use the API:

```bash
#!/bin/bash

# 1. Login and get token
echo "1. Logging in..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "password": "demo123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Get user profile
echo -e "\n2. Getting user profile..."
curl -s -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# 3. Parse SMS transaction
echo -e "\n3. Parsing SMS transaction..."
curl -s -X POST http://localhost:8000/api/v1/transactions/sms \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sms_text": "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy"}' \
  | jq '.'

# 4. Get dashboard
echo -e "\n4. Getting dashboard..."
curl -s -X GET http://localhost:8000/api/v1/dashboard \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# 5. Chat with AI
echo -e "\n5. Chatting with AI..."
curl -s -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr_9876543210",
    "phone": "+919876543210",
    "metadata": {"name": "Rahul", "balance": 12000},
    "message": "How much did I spend on food?",
    "provider": "openai"
  }' \
  | jq '.'

# 6. Get weekly report
echo -e "\n6. Getting weekly report..."
curl -s -X GET http://localhost:8000/api/v1/reports/weekly \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

echo -e "\nWorkflow complete!"
```

---

## Rate Limiting

Currently, no rate limiting is implemented. For production deployment, consider adding rate limiting middleware.

## CORS

Configure CORS settings in `app/main.py` to allow requests from your mobile app domain.

## WebSocket Support

WebSocket support for real-time updates is not currently implemented but can be added using FastAPI's WebSocket support.

---

## Support

For issues or questions, refer to the project README or contact the development team.
