# KIVI Backend - Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   
   Create a `.env` file in the project root (or use the existing one):
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

## Running the Application

### Development Mode (with auto-reload)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Python directly

```bash
python -m app.main
```

## Access the API

Once the server is running:

- **API Root:** http://localhost:8000/
- **Interactive API Docs (Swagger):** http://localhost:8000/docs
- **Alternative API Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## Quick Test

Test the health check endpoint:

```bash
curl http://localhost:8000/health
```

## Available Endpoints

### Authentication
- `POST /api/v1/login` - User login and JWT token generation

### User Profile
- `GET /api/v1/users/me` - Get authenticated user profile
- `PUT /api/v1/users/me` - Update user profile

### Finance
- `GET /api/v1/transactions` - Get transaction history
- `POST /api/v1/transactions` - Create manual transaction
- `POST /api/v1/transactions/sms` - Parse SMS and create transaction
- `GET /api/v1/dashboard` - Get financial dashboard
- `GET /api/v1/reports/weekly` - Get weekly report
- `GET /api/v1/reports/monthly` - Get monthly report

### WhatsApp
- `POST /api/v1/whatsapp/webhook` - WhatsApp webhook (called by Meta)
- `POST /api/v1/whatsapp/send_notification` - Send WhatsApp notification

### AI Chat
- `POST /api/v1/ai/chat` - Chat with AI (mobile app)
- `GET /api/v1/ai/health` - AI service health check



## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`, ensure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### Port Already in Use

If port 8000 is already in use, specify a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

### Database Connection Errors

Ensure MongoDB is running and the MONGO_URI in your .env file is correct.

## Next Steps

- Read the full documentation in `docs/API_ENDPOINTS.md`
- Check the project structure in `README.md`
- Review the design document in `.kiro/specs/kivi-backend/design.md`
- Explore the requirements in `.kiro/specs/kivi-backend/requirements.md`
