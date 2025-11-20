# Design Document

## Overview

KIVI Backend is a FastAPI-based microservice architecture designed for the KIVI hackathon project, specifically targeting gig workers with uncertain income streams. The system provides a comprehensive financial management platform with AI-powered chat capabilities, WhatsApp integration, SMS transaction processing, and intelligent notification system tailored for freelancers, delivery partners, ride-share drivers, and other gig economy workers. The architecture follows functional programming principles with modular, pluggable components.

### Target User: Gig Workers

The system is designed for users with:
- **Uncertain Income**: Variable earnings from multiple sources (Uber, Swiggy, Zomato, freelance projects)
- **Irregular Cash Flow**: Income arrives at unpredictable intervals
- **Multiple Income Streams**: Earnings from different platforms and clients
- **Limited Financial Literacy**: Need simple, conversational guidance
- **Mobile-First**: Primarily use smartphones for work and finance management
- **WhatsApp Preference**: Comfortable with WhatsApp as primary communication channel

### Key Design Principles

1. **Functional Programming**: Pure functions, minimal classes, module-level functions
2. **Modularity**: Pluggable AI providers, swappable data stores (mock → MongoDB)
3. **Async-First**: All I/O operations use async/await for optimal performance
4. **Separation of Concerns**: Clear boundaries between API, services, models, and utilities
5. **Hackathon-Friendly**: Simple, well-documented code with mock data support

### Technology Stack

- **Framework**: FastAPI (async Python web framework)
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT with PyJWT
- **HTTP Client**: httpx (async)
- **AI Providers**: OpenAI GPT, Anthropic Claude
- **Messaging**: Meta WhatsApp Cloud API
- **Logging**: Python logging with colored console output

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────┐         ┌──────────────────┐
│  Mobile App     │────────▶│   FastAPI App    │
│  (Chat UI)      │         │   (main.py)      │
└─────────────────┘         └────────┬─────────┘
                                     │
┌─────────────────┐                  │
│  WhatsApp       │────────▶         │
│  (Meta Cloud)   │                  │
└─────────────────┘                  │
                                     ▼
                    ┌──────────────────────────┐
                    │   API Routes Layer       │
                    │  (/api/v1/routes_*.py)   │
                    └────────┬─────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  Services   │  │  AI Chat    │  │  WhatsApp   │
    │  Layer      │  │  Service    │  │  Service    │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                │
           │                ▼                │
           │      ┌──────────────────┐       │
           │      │  AI Providers    │       │
           │      │  (OpenAI/Claude) │       │
           │      └──────────────────┘       │
           │                                 │
           ▼                                 ▼
    ┌──────────────────────────────────────────┐
    │         Data Access Layer                │
    │  (Models + Mock/MongoDB Abstraction)     │
    └────────────────┬─────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    ┌─────────┐           ┌──────────┐
    │  Mock   │           │ MongoDB  │
    │  Data   │           │ (Motor)  │
    └─────────┘           └──────────┘
```

### Request Flow Examples

**WhatsApp Message Flow:**
1. Meta sends webhook POST → `/webhook`
2. Extract phone, user_id, message
3. Persist user message → message_logs
4. Build context from user profile
5. Call `chat_with_model(metadata, message, "openai")`
6. AI provider returns response
7. Persist bot message → message_logs
8. Send reply via Meta API

**Mobile App Chat Flow:**
1. App sends POST → `/chat`
2. Authenticate JWT token
3. Call `chat_with_model(metadata, message, provider)`
4. Persist user + bot messages
5. Return response to app

**SMS Transaction Flow:**
1. App sends POST → `/transactions/sms`
2. Parse SMS text → extract amount, vendor, timestamp
3. Classify transaction → category
4. Persist to transactions collection
5. Evaluate rule engine → check triggers
6. Send notification if rule matched

## Components and Interfaces

### 1. API Routes Layer

#### routes_auth.py
```python
POST /login
  Request: { "phone": str, "password": str }
  Response: { "access_token": str, "token_type": "bearer" }
```

#### routes_user.py
```python
GET /users/me
  Headers: Authorization: Bearer <token>
  Response: { user profile object }

PUT /users/me
  Headers: Authorization: Bearer <token>
  Request: { profile fields }
  Response: { updated user profile }
```

#### routes_finance.py
```python
GET /transactions
  Headers: Authorization: Bearer <token>
  Query: ?start_date=...&end_date=...&category=...
  Response: { "transactions": [...] }

POST /transactions
  Request: { "amount": float, "vendor": str, "category": str, ... }
  Response: { created transaction }

POST /transactions/sms
  Request: { "sms_text": str }
  Response: { "transaction": {...}, "category": str }

GET /dashboard
  Response: { "balance": float, "monthly_spending": float, "categories": {...}, "budgets": [...] }

GET /reports/weekly
  Response: { "total_spent": float, "top_categories": [...], "comparison": {...} }

GET /reports/monthly
  Response: { "total_spent": float, "category_trends": {...}, "budget_adherence": [...] }
```

#### routes_whatsapp.py
```python
POST /webhook
  Request: Meta webhook payload
  Response: 200 OK (quick ack)

POST /send_notification
  Request: { "phone": str, "text": str, "provider": str }
  Response: { "status": "sent", "message_id": str }
```

#### routes_ai.py
```python
POST /chat
  Request: { "user_id": str, "phone": str, "metadata": {...}, "message": str, "provider": str }
  Response: { "reply": str, "provider": str, "usage": {...} }
```

### 2. Services Layer

#### ai_chat.py
Core chat function that serves both WhatsApp and mobile app:

```python
async def chat_with_model(
    metadata: dict,
    message: str,
    provider: str = "openai"
) -> dict:
    """
    Single-use chat function for conversational AI.
    
    Args:
        metadata: User context (name, job, goals, transaction_summary)
        message: User's message text
        provider: "openai" or "anthropic"
    
    Returns:
        {
            "reply": str,
            "provider": str,
            "usage": dict
        }
    """
    # Build prompt with metadata context
    # Route to provider
    # Log prompt and response
    # Return structured response
```

#### whatsapp_service.py
```python
async def handle_incoming_webhook(db, payload: dict) -> None:
    """Process incoming WhatsApp message and respond."""
    # Validate webhook
    # Extract phone, user_id, message
    # Get user profile for metadata
    # Persist user message
    # Call chat_with_model
    # Persist bot message
    # Send reply via Meta API

async def send_whatsapp_text(phone: str, text: str) -> dict:
    """Send WhatsApp message via Meta Cloud API."""
    # Build Meta API payload
    # POST to Graph API
    # Handle errors
    # Return status
```

#### sms_parser.py
```python
def parse_sms(text: str) -> dict:
    """
    Extract transaction details from SMS text.
    
    Returns:
        {
            "amount": float,
            "vendor": str,
            "timestamp": str,
            "transaction_type": "debit" | "credit"
        }
    """
    # Regex patterns for amount
    # Extract vendor name
    # Parse date/time
    # Determine debit/credit
```

#### expense_analyzer.py
```python
def categorize_transaction(txn: dict) -> str:
    """Classify transaction into category using keyword matching."""
    # Categories: food, transport, shopping, bills, entertainment, healthcare, education, others
    # Keyword matching on vendor field
    # Return category string

def summarize_transactions(transactions: list) -> dict:
    """Aggregate transactions by category."""
    # Group by category
    # Sum amounts
    # Return category totals
```

#### nudge_engine.py
```python
def generate_nudges(user: dict, transactions: list) -> list[str]:
    """Generate rule-based financial nudges for gig workers."""
    # Check low balance (critical for gig workers)
    # Check budget exceeded
    # Check unusual spending
    # Check savings goal progress
    # Check income volatility (low earning days)
    # Check emergency fund adequacy
    # Suggest income diversification
    # Return list of nudge messages

async def evaluate_rules(db, user_id: str, transaction: dict) -> None:
    """Evaluate user rules and trigger notifications."""
    # Get active rules for user
    # Check conditions against transaction
    # Create notification record
    # Send WhatsApp message if triggered

def generate_gig_worker_insights(user: dict, transactions: list) -> dict:
    """Generate insights specific to gig workers."""
    # Income pattern analysis (best earning days/hours)
    # Platform comparison (which platform pays better)
    # Expense optimization for gig work (fuel, maintenance)
    # Emergency fund runway (months of expenses covered)
    # Return structured insights
```

#### aa_service.py
```python
async def fetch_aa_data(user_id: str) -> dict:
    """Placeholder for Account Aggregator integration."""
    # Future: Real AA API integration
    # For now: Return sample data

def normalize_aa_data(raw_data: dict) -> dict:
    """Transform AA data to internal format."""
    # Normalize transaction format
    # Extract account balances
    # Return standardized structure
```

### 3. AI Providers

#### ai_providers/openai_provider.py
```python
async def call_openai(prompt: str) -> str:
    """
    Call OpenAI API with prompt.
    
    Returns response text.
    Mocked if no API key configured.
    """
    # Check for OPENAI_API_KEY
    # If present: Real API call
    # If absent: Return mock response
    # Include commented real implementation

async def call_openai_real(prompt: str, api_key: str) -> str:
    """Real OpenAI API implementation (commented example)."""
    # POST to https://api.openai.com/v1/chat/completions
    # Model: gpt-4 or gpt-3.5-turbo
    # Return assistant message
```

#### ai_providers/anthropic_provider.py
```python
async def call_anthropic(prompt: str) -> str:
    """
    Call Anthropic API with prompt.
    
    Returns response text.
    Mocked if no API key configured.
    """
    # Check for ANTHROPIC_API_KEY
    # If present: Real API call
    # If absent: Return mock response
    # Include commented real implementation
```

### 4. Data Models

#### user_model.py
```python
class UserProfile(BaseModel):
    user_id: str
    phone: str
    name: str
    email: Optional[str]
    job: Optional[str]  # e.g., "Delivery Partner", "Freelance Designer", "Uber Driver"
    city: Optional[str]
    gig_platforms: list[str]  # ["Swiggy", "Zomato", "Uber", "Upwork"]
    financial_summary: dict  # balance, avg_monthly_income, monthly_expenses, income_volatility
    budgets: list[dict]  # category budgets
    goals: list[dict]  # savings goals (emergency fund, bike EMI, etc.)
    notification_preferences: dict
    created_at: str
    updated_at: str

async def get_user_by_phone(db, phone: str) -> Optional[dict]:
    """Retrieve user by phone number."""

async def upsert_user(db, user_dict: dict) -> dict:
    """Create or update user profile."""

async def create_sample_user(phone: str) -> dict:
    """Create user with sample AA data for onboarding (gig worker profile)."""
```

#### transaction_model.py
```python
class Transaction(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    vendor: str
    category: str
    transaction_type: str  # debit/credit
    timestamp: str
    source: str  # sms, aa, manual
    raw_sms_text: Optional[str]
    metadata: dict

async def get_transactions(
    db,
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None
) -> list[dict]:
    """Query transactions with filters."""

async def create_transaction(db, txn: dict) -> dict:
    """Insert new transaction."""
```

#### message_log_model.py
```python
class MessageLog(BaseModel):
    message_id: str
    user_id: str
    phone: str
    metadata: dict
    role: str  # user | bot
    text: str
    provider: Optional[str]
    timestamp: str

def create_message_doc(
    user_id: str,
    phone: str,
    metadata: dict,
    role: str,
    text: str,
    model: Optional[str] = None
) -> dict:
    """Create message document for insertion."""

async def save_message(db, message_doc: dict) -> None:
    """Persist message to database."""

async def get_conversation_history(
    db,
    user_id: str,
    limit: int = 50
) -> list[dict]:
    """Retrieve recent messages for user."""
```

#### session_model.py
```python
class Session(BaseModel):
    session_id: str
    user_id: str
    refresh_token: str
    created_at: str
    expires_at: str

async def create_session(db, user_id: str, refresh_token: str) -> dict:
    """Store session with refresh token."""

async def get_session(db, session_id: str) -> Optional[dict]:
    """Retrieve session."""
```

### 5. Core Modules

#### core/config.py
```python
# Environment variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "placeholder")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "placeholder")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "kivi-verify-token")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# Reference to project brief
PROJECT_BRIEF = "/mnt/data/MumbaiHacks 2025.pdf"
```

#### core/security.py
```python
def create_token(user_id: str, phone: str) -> str:
    """Generate JWT token."""
    # Payload: user_id, phone, exp
    # Sign with JWT_SECRET
    # Return token string

def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""
    # Decode with JWT_SECRET
    # Check expiration
    # Return payload or raise exception

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency for authentication."""
    # Verify token
    # Return user info
```

#### core/logging_config.py
```python
def setup_logging():
    """Configure logging with colored console output."""
    # Format: timestamp | level | module:function | message
    # Colors: DEBUG=blue, INFO=green, WARNING=yellow, ERROR=red
    # Include exception tracebacks
    # Log to console (stdout)

# Logger instances
logger = logging.getLogger("kivi")
ai_logger = logging.getLogger("kivi.ai")
webhook_logger = logging.getLogger("kivi.webhook")
db_logger = logging.getLogger("kivi.db")
```

#### core/exceptions.py
```python
class KiviException(Exception):
    """Base exception for KIVI system."""

class AuthenticationError(KiviException):
    """Authentication failed."""

class WhatsAppAPIError(KiviException):
    """WhatsApp API call failed."""

class AIProviderError(KiviException):
    """AI provider call failed."""

def http_exception_handler(exc: Exception) -> JSONResponse:
    """Convert exceptions to HTTP responses."""
```

### 6. Database Layer

#### db/mongodb.py
```python
from motor.motor_asyncio import AsyncIOMotorClient

client: Optional[AsyncIOMotorClient] = None

async def connect_db():
    """Initialize MongoDB connection."""
    global client
    client = AsyncIOMotorClient(MONGO_URI)
    # Test connection
    await client.admin.command('ping')

async def close_db():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()

def get_db():
    """Get database instance."""
    if USE_MOCK_DATA:
        return MockDatabase()
    return client.kivi_db

class MockDatabase:
    """In-memory mock database for development."""
    def __init__(self):
        self.users = []
        self.transactions = []
        self.message_logs = []
        self.notifications = []
        self.user_rules = []
    
    # Implement collection-like interface
```

### 7. Utilities

#### utils/helpers.py
```python
def format_currency(amount: float, currency: str = "INR") -> str:
    """Format amount with currency symbol."""
    # ₹1,234.56

def safe_get(d: dict, key: str, default=None):
    """Safe dictionary access with default."""

def generate_id(prefix: str = "") -> str:
    """Generate unique ID."""
    # prefix_timestamp_random
```

#### utils/date_utils.py
```python
def now_iso() -> str:
    """Current timestamp in ISO 8601 format."""

def parse_date(date_str: str) -> datetime:
    """Parse various date formats."""

def get_week_range() -> tuple[str, str]:
    """Get start and end of current week."""

def get_month_range() -> tuple[str, str]:
    """Get start and end of current month."""
```

#### utils/http_client.py
```python
async def make_request(
    method: str,
    url: str,
    headers: dict = None,
    json: dict = None,
    retries: int = 3
) -> dict:
    """Async HTTP request with retry logic."""
    # Use httpx.AsyncClient
    # Retry on 5xx errors
    # Exponential backoff
    # Log requests/responses
```

#### utils/jwt_handler.py
```python
def encode_jwt(payload: dict) -> str:
    """Encode JWT token."""

def decode_jwt(token: str) -> dict:
    """Decode and verify JWT token."""
```

## Data Models

### MongoDB Collections Schema

#### users Collection
```json
{
  "_id": "ObjectId",
  "user_id": "usr_1234567890",
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
    },
    {
      "goal_id": "goal_002",
      "name": "Bike EMI Buffer",
      "target_amount": 15000.00,
      "current_amount": 5000.00,
      "deadline": "2025-03-31",
      "priority": "medium"
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

**Indexes:**
- `phone` (unique)
- `user_id` (unique)

#### transactions Collection
```json
{
  "_id": "ObjectId",
  "transaction_id": "txn_1234567890",
  "user_id": "usr_1234567890",
  "amount": 450.00,
  "vendor": "Swiggy",
  "category": "food",
  "transaction_type": "debit",
  "timestamp": "2025-01-20T19:30:00Z",
  "source": "sms",
  "raw_sms_text": "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy",
  "metadata": {
    "payment_method": "UPI",
    "location": "Mumbai"
  }
}
```

**Indexes:**
- `user_id` + `timestamp` (compound)
- `user_id` + `category`
- `timestamp`

#### message_logs Collection
```json
{
  "_id": "ObjectId",
  "message_id": "msg_1234567890",
  "user_id": "usr_1234567890",
  "phone": "+919876543210",
  "metadata": {
    "name": "Rahul",
    "balance": 45000,
    "recent_spending": 5200
  },
  "role": "user",
  "text": "How much did I spend on food this month?",
  "provider": null,
  "timestamp": "2025-01-20T20:15:00Z"
}
```

**Indexes:**
- `user_id` + `timestamp` (compound)
- `user_id` + `role`

#### notifications Collection
```json
{
  "_id": "ObjectId",
  "notification_id": "notif_1234567890",
  "user_id": "usr_1234567890",
  "trigger_type": "budget_exceeded",
  "rule_id": "rule_001",
  "message": "You've exceeded your food budget by ₹200 this month.",
  "status": "sent",
  "timestamp": "2025-01-20T21:00:00Z",
  "metadata": {
    "category": "food",
    "budget_limit": 8000,
    "current_spent": 8200
  }
}
```

**Indexes:**
- `user_id` + `timestamp`
- `status`

#### user_rules Collection
```json
{
  "_id": "ObjectId",
  "rule_id": "rule_001",
  "user_id": "usr_1234567890",
  "rule_type": "budget_exceeded",
  "conditions": {
    "category": "food",
    "threshold_percentage": 100
  },
  "threshold_values": {
    "budget_limit": 8000
  },
  "active": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Indexes:**
- `user_id` + `active`
- `rule_type`

### Mock Data Structure

For initial development without MongoDB:

```python
MOCK_USERS = {
    "+919876543210": {
        "user_id": "usr_mock_001",
        "phone": "+919876543210",
        "name": "Demo User",
        # ... full user object
    }
}

MOCK_TRANSACTIONS = [
    {
        "transaction_id": "txn_mock_001",
        "user_id": "usr_mock_001",
        # ... transaction fields
    }
]

MOCK_MESSAGE_LOGS = []
MOCK_NOTIFICATIONS = []
MOCK_USER_RULES = []
```

## Error Handling

### Error Handling Strategy

1. **API Layer**: Return appropriate HTTP status codes
   - 400: Bad Request (validation errors)
   - 401: Unauthorized (auth failures)
   - 404: Not Found
   - 500: Internal Server Error

2. **Service Layer**: Raise custom exceptions
   - `AuthenticationError`
   - `WhatsAppAPIError`
   - `AIProviderError`
   - Log errors with full context

3. **Database Layer**: Wrap operations in try-except
   - Log database errors
   - Return None or raise exception
   - Graceful degradation to mock data

4. **External APIs**: Retry logic with exponential backoff
   - Max 3 retries
   - Log all attempts
   - Return error response if all retries fail

### Logging Strategy

```python
# Function entry
logger.debug(f"Entering function_name with params: {params}")

# API calls
webhook_logger.info(f"Received webhook from {phone}: {message[:50]}")

# AI interactions
ai_logger.debug(f"Prompt to {provider}: {prompt}")
ai_logger.info(f"Response from {provider} (latency: {latency}ms): {response[:100]}")

# Database operations
db_logger.debug(f"Querying transactions for user {user_id}")

# Errors
logger.error(f"Failed to send WhatsApp message: {error}", exc_info=True)
```

## Testing Strategy

### Manual Testing Approach

1. **API Endpoints**: Use curl commands (documented in docs/API_ENDPOINTS.md)
2. **WhatsApp Webhook**: Use ngrok + Meta webhook testing tool
3. **AI Chat**: Test via POST /chat endpoint with sample data
4. **SMS Parsing**: Test with real SMS examples
5. **Rule Engine**: Create test transactions and verify notifications

### Sample Data

Provide sample JSON files in `docs/samples/` with gig worker context:
- `sample_user.json` (delivery partner profile)
- `sample_transactions.json` (Swiggy/Zomato earnings, fuel expenses, etc.)
- `sample_sms_messages.json` (payment notifications from gig platforms)
- `sample_webhook_payload.json` (WhatsApp conversation examples)
- `sample_gig_worker_scenarios.json` (various gig worker personas)

## Deployment Considerations

### Environment Variables (.env)

```bash
# MongoDB
MONGO_URI=mongodb://localhost:27017
USE_MOCK_DATA=true

# JWT
JWT_SECRET=your-secret-key-here
JWT_EXPIRATION_HOURS=24

# WhatsApp
WHATSAPP_TOKEN=your-meta-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-id
WHATSAPP_VERIFY_TOKEN=kivi-verify-token

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Logging
LOG_LEVEL=DEBUG
```

### Git Branching Strategy

- **prod**: Production-ready code
- **uat**: User acceptance testing
- **dev**: Active development (default)
- **feature/***: Feature branches created from dev

### Development Workflow

1. Create feature branch from dev: `git checkout -b feature/task-name`
2. Implement feature
3. Commit with clear message: `git commit -m "feat: implement SMS parsing"`
4. Push feature branch: `git push origin feature/task-name`
5. Merge to dev after validation
6. Promote to uat → prod when ready

## Security Considerations

1. **JWT Tokens**: Short expiration (24h), secure secret
2. **WhatsApp Webhook**: Verify signature/token
3. **API Keys**: Never commit to git, use .env
4. **Input Validation**: Pydantic models for all inputs
5. **SQL Injection**: N/A (MongoDB, but use parameterized queries)
6. **Rate Limiting**: Consider adding for production
7. **CORS**: Configure for mobile app domain

## Performance Optimizations

1. **Async Operations**: All I/O is async
2. **Database Indexes**: Compound indexes on frequent queries
3. **Caching**: 1-hour TTL for dashboard/reports
4. **Connection Pooling**: Motor handles MongoDB connections
5. **Lazy Loading**: Load user context only when needed

## Future Enhancements

1. **Real Account Aggregator Integration**: Replace sample data
2. **Advanced AI Features**: Summarization, analysis, predictions
3. **Push Notifications**: Firebase for mobile app
4. **Multi-language Support**: i18n for messages
5. **Analytics Dashboard**: Admin panel for system metrics
6. **Webhook Retry Logic**: Queue failed WhatsApp messages
7. **User Preferences**: Customizable notification rules
8. **Export Data**: CSV/PDF reports

## Documentation Structure

```
docs/
├── API_ENDPOINTS.md          # Complete API documentation with curl examples
├── SETUP.md                  # Development setup instructions
├── DEPLOYMENT.md             # Deployment guide
├── ARCHITECTURE.md           # Detailed architecture diagrams
└── samples/
    ├── sample_user.json
    ├── sample_transactions.json
    ├── sample_sms_messages.json
    └── sample_webhook_payload.json
```

## Project Structure Summary

```
kivi-backend/
├── app/
│   ├── api/v1/              # API routes
│   ├── core/                # Config, security, logging
│   ├── services/            # Business logic
│   ├── models/              # Data models
│   ├── utils/               # Utilities
│   ├── db/                  # Database connection
│   └── main.py              # FastAPI app
├── docs/                    # Documentation
├── .env                     # Environment variables
├── .gitignore              # Git ignore rules
├── requirements.txt         # Python dependencies
└── README.md               # Project overview
```
