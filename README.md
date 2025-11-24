# KIVI Backend

**AI-Powered Financial Assistant for Gig Workers**

KIVI Backend is a FastAPI-based microservice built for the KIVI hackathon project, providing intelligent financial management for India's gig economy workers. The system integrates WhatsApp messaging, AI chat capabilities, SMS transaction parsing, and personalized financial insights tailored for delivery partners, ride-share drivers, freelancers, and other gig workers with uncertain income streams.

## 🎯 Target Audience: Gig Workers

KIVI is specifically designed for users in the gig economy who face unique financial challenges:

### Who We Serve
- **Delivery Partners**: Swiggy, Zomato, Dunzo riders
- **Ride-Share Drivers**: Uber, Ola drivers
- **Freelancers**: Upwork, Fiverr professionals
- **Platform Workers**: Urban Company, Housejoy service providers

### Their Challenges
- **Uncertain Income**: Variable earnings that fluctuate daily/weekly
- **Multiple Income Streams**: Earnings from 2-3 different platforms
- **Irregular Cash Flow**: Income arrives at unpredictable intervals
- **Limited Financial Literacy**: Need simple, conversational guidance
- **Mobile-First**: Primarily use smartphones for work and finance
- **WhatsApp Preference**: Comfortable with WhatsApp as primary communication

### How KIVI Helps
- **Income Pattern Analysis**: Identify best earning days/hours across platforms
- **Platform Comparison**: Compare which gig platforms pay better
- **Emergency Fund Tracking**: Calculate runway (months of expenses covered)
- **Expense Optimization**: Track gig-specific costs (fuel, maintenance, platform fees)
- **Conversational AI**: Get financial advice through natural WhatsApp chat
- **SMS Auto-Parsing**: Automatically categorize transactions from bank SMS
- **Proactive Nudges**: Receive alerts for low balance, budget exceeded, savings goals

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- (Optional) MongoDB for production use

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd kivi-backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   
   Create a `.env` file in the project root:
   ```bash
   # MongoDB
   MONGO_URI=mongodb://localhost:27017

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

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API:**
   - API Root: http://localhost:8000/
   - Interactive Docs: http://localhost:8000/docs
   - API Documentation: http://localhost:8000/redoc

### Quick Test

Test the health check endpoint:

```bash
curl http://localhost:8000/health
```

## 📚 Sample API Usage

### 1. Parse SMS Transaction

```bash
curl -X POST http://localhost:8000/api/v1/transactions/sms \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sms_text": "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy"
  }'
```

### 2. Chat with AI

```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr_9876543210",
    "phone": "+919876543210",
    "message": "How much did I spend on food this month?",
    "provider": "openai"
  }'
```

### 3. Get Financial Dashboard

```bash
curl -X GET http://localhost:8000/api/v1/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

For complete API documentation with all endpoints, see [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md).

## 🏗️ Project Structure

```
kivi-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── routes_auth.py       # Authentication endpoints
│   │       ├── routes_user.py       # User profile management
│   │       ├── routes_finance.py    # Transaction & dashboard endpoints
│   │       ├── routes_whatsapp.py   # WhatsApp webhook & notifications
│   │       └── routes_ai.py         # AI chat endpoints
│   ├── core/
│   │   ├── config.py                # Configuration management
│   │   ├── security.py              # JWT authentication
│   │   ├── logging_config.py        # Logging setup
│   │   └── exceptions.py            # Custom exceptions
│   ├── services/
│   │   ├── ai_chat.py               # Core AI chat service
│   │   ├── whatsapp_service.py      # WhatsApp integration
│   │   ├── sms_parser.py            # SMS transaction parsing
│   │   ├── expense_analyzer.py      # Transaction categorization
│   │   ├── nudge_engine.py          # Financial insights & alerts
│   │   ├── aa_service.py            # Account Aggregator (placeholder)
│   │   └── ai_providers/
│   │       ├── openai_provider.py   # OpenAI integration
│   │       └── anthropic_provider.py # Anthropic integration
│   ├── models/
│   │   ├── user_model.py            # User profile data model
│   │   ├── transaction_model.py     # Transaction data model
│   │   ├── message_log_model.py     # Chat message logging
│   │   └── session_model.py         # JWT session management
│   ├── utils/
│   │   ├── helpers.py               # Utility functions
│   │   ├── date_utils.py            # Date/time utilities
│   │   ├── http_client.py           # HTTP client with retry
│   │   └── jwt_handler.py           # JWT encoding/decoding
│   ├── db/
│   │   └── mongodb.py               # MongoDB connection & mock data
│   └── main.py                      # FastAPI application entry point
├── docs/
│   ├── API_ENDPOINTS.md             # Complete API documentation
│   └── samples/                     # Sample JSON files
│       ├── sample_user.json
│       ├── sample_transactions.json
│       ├── sample_sms_messages.json
│       ├── sample_webhook_payload.json
│       └── sample_gig_worker_scenarios.json
├── .kiro/specs/kivi-backend/
│   ├── requirements.md              # Feature requirements (EARS format)
│   ├── design.md                    # Architecture & design document
│   └── tasks.md                     # Implementation task list
├── .env                             # Environment variables (not in git)
├── .gitignore                       # Git ignore rules
├── requirements.txt                 # Python dependencies
├── QUICKSTART.md                    # Quick start guide
└── README.md                        # This file
```

## 🔧 Configuration

### MongoDB Configuration

KIVI uses MongoDB for persistent data storage:

- **Requirements**:
  - MongoDB installed and running
  - Valid `MONGO_URI` in `.env`
- **Benefits**:
  - Persistent data storage
  - Production-ready
  - Supports complex queries and aggregations

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017` | Yes |
| `JWT_SECRET` | Secret key for JWT signing | `dev-secret-key` | Yes |
| `JWT_EXPIRATION_HOURS` | JWT token expiration | `24` | No |
| `WHATSAPP_TOKEN` | Meta WhatsApp API token | `placeholder` | Yes (for WhatsApp) |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID | `placeholder` | Yes (for WhatsApp) |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verification token | `kivi-verify-token` | Yes (for WhatsApp) |
| `OPENAI_API_KEY` | OpenAI API key | `""` | No (uses mock) |
| `ANTHROPIC_API_KEY` | Anthropic API key | `""` | No (uses mock) |
| `LOG_LEVEL` | Logging level | `DEBUG` | No |

## 🌿 Git Branching Strategy

KIVI follows a structured Git workflow with three main branches:

### Branch Structure

```
prod (production)
  ↑
uat (user acceptance testing)
  ↑
dev (development - default)
  ↑
feature/* (feature branches)
```

### Branch Descriptions

- **`prod`**: Production-ready code, deployed to production environment
- **`uat`**: User acceptance testing, deployed to staging environment
- **`dev`**: Active development branch, default branch for all development
- **`feature/*`**: Feature branches created from `dev` for individual tasks

### Development Workflow

1. **Start a new feature:**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/task-name
   ```

2. **Implement the feature:**
   ```bash
   # Make your changes
   git add .
   git commit -m "feat: implement task description"
   ```

3. **Push feature branch:**
   ```bash
   git push origin feature/task-name
   ```

4. **Merge to dev:**
   ```bash
   git checkout dev
   git merge feature/task-name
   git push origin dev
   ```

5. **Promote to UAT (when ready):**
   ```bash
   git checkout uat
   git merge dev
   git push origin uat
   ```

6. **Deploy to production (after UAT approval):**
   ```bash
   git checkout prod
   git merge uat
   git push origin prod
   ```

### Commit Message Convention

Follow conventional commits format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```bash
git commit -m "feat: add SMS transaction parsing"
git commit -m "fix: resolve JWT token expiration issue"
git commit -m "docs: update API endpoint documentation"
```

## 🏃 Running the Application

### Development Mode (with auto-reload)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode (with multiple workers)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Python directly

```bash
python -m uvicorn app.main:app --reload
```



## 📖 API Endpoints

### Authentication
- `POST /api/v1/login` - User login and JWT token generation

### User Profile
- `GET /api/v1/users/me` - Get authenticated user profile
- `PUT /api/v1/users/me` - Update user profile

### Finance
- `GET /api/v1/transactions` - Get transaction history with filters
- `POST /api/v1/transactions` - Create manual transaction
- `POST /api/v1/transactions/sms` - Parse SMS and create transaction
- `GET /api/v1/dashboard` - Get financial dashboard
- `GET /api/v1/reports/weekly` - Get weekly spending report
- `GET /api/v1/reports/monthly` - Get monthly spending report

### WhatsApp
- `POST /api/v1/whatsapp/webhook` - WhatsApp webhook (called by Meta)
- `POST /api/v1/whatsapp/send_notification` - Send WhatsApp notification

### AI Chat
- `POST /api/v1/ai/chat` - Chat with AI (mobile app)
- `GET /api/v1/ai/health` - AI service health check

For detailed API documentation with request/response schemas and curl examples, see [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md).

## 🧪 Testing

### Manual Testing

Use the provided curl commands in the documentation:

```bash
# Test health check
curl http://localhost:8000/health

# Test SMS parsing (requires authentication)
curl -X POST http://localhost:8000/api/v1/transactions/sms \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sms_text": "Rs 450 debited from A/c XX1234 on 20-Jan-25 to Swiggy"}'
```

### Sample Data

Sample JSON files are available in `docs/samples/`:
- `sample_user.json` - Gig worker user profile
- `sample_transactions.json` - Transaction examples
- `sample_sms_messages.json` - SMS parsing examples
- `sample_webhook_payload.json` - WhatsApp webhook examples
- `sample_gig_worker_scenarios.json` - Various gig worker personas

## 🔍 Key Features

### 1. WhatsApp Integration
- Receive messages via Meta Cloud API webhook
- Send proactive notifications
- Conversational AI responses
- Message logging for audit trail

### 2. AI Chat Service
- Pluggable AI providers (OpenAI, Anthropic)
- Context-aware responses using user metadata
- Supports both WhatsApp and mobile app
- Mocked responses for development

### 3. SMS Transaction Parsing
- Automatic extraction of amount, vendor, timestamp
- Support for multiple bank SMS formats
- Transaction type detection (debit/credit)
- Category classification

### 4. Expense Analysis
- Keyword-based transaction categorization
- Gig-specific categories (fuel, maintenance, platform fees)
- Spending summaries by category
- Budget tracking

### 5. Intelligent Nudges
- Low balance alerts
- Budget exceeded notifications
- Unusual spending detection
- Savings goal progress tracking
- Gig worker insights (income patterns, platform comparison)

### 6. Gig Worker Insights
- Income pattern analysis (best earning days/hours)
- Platform comparison (which pays better)
- Emergency fund runway calculation
- Expense optimization suggestions

## 🛠️ Technology Stack

- **Framework**: FastAPI (async Python web framework)
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT with PyJWT
- **HTTP Client**: httpx (async)
- **AI Providers**: OpenAI GPT, Anthropic Claude
- **Messaging**: Meta WhatsApp Cloud API
- **Logging**: Python logging with colored console output
- **Validation**: Pydantic models

## 📝 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)** - Complete API documentation
- **[.kiro/specs/kivi-backend/requirements.md](.kiro/specs/kivi-backend/requirements.md)** - Feature requirements
- **[.kiro/specs/kivi-backend/design.md](.kiro/specs/kivi-backend/design.md)** - Architecture & design
- **[.kiro/specs/kivi-backend/tasks.md](.kiro/specs/kivi-backend/tasks.md)** - Implementation tasks

## 🐛 Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
```bash
pip install -r requirements.txt
```

### Port Already in Use

Specify a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

### Database Connection Errors

Check your `MONGO_URI` in the .env file and ensure MongoDB is running.

### WhatsApp Webhook Not Receiving Messages

1. Ensure your server is publicly accessible (use ngrok for local testing)
2. Verify `WHATSAPP_VERIFY_TOKEN` matches Meta's configuration
3. Check webhook logs in the console

### AI Provider Errors

Ensure AI provider API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY) are configured in your .env file.

## 🚀 Deployment

### Environment Setup

1. Configure production MongoDB URI
2. Set strong `JWT_SECRET`
3. Configure WhatsApp API credentials
4. Add AI provider API keys
5. Set `LOG_LEVEL=INFO` or `WARNING`

### Production Considerations

- Use multiple workers: `--workers 4`
- Enable HTTPS/TLS
- Configure CORS for mobile app domain
- Set up monitoring and logging
- Implement rate limiting
- Use environment-specific `.env` files

## 🤝 Contributing

This is a hackathon project. For development:

1. Create a feature branch from `dev`
2. Implement your changes
3. Test thoroughly
4. Commit with clear messages
5. Merge to `dev` after validation

## 📄 License

This project is built for the KIVI hackathon.

## 🙏 Acknowledgments

Built for the KIVI hackathon project to empower India's gig economy workers with AI-powered financial management.

---

**For detailed setup instructions, see [QUICKSTART.md](QUICKSTART.md)**

**For complete API documentation, see [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)**
