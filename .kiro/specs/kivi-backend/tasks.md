# Implementation Plan

- [ ] 1. Initialize project structure and Git repository
  - Create kivi-backend directory with complete folder structure (app/api/v1, app/core, app/services, app/models, app/utils, app/db, docs)
  - Create .gitignore file excluding .env, __pycache__, *.pyc, venv/, .vscode/
  - Initialize Git repository with git init
  - Create initial commit with project structure
  - Create GitHub repository and add as remote
  - Create three branches (prod, uat, dev) and push all to GitHub
  - Set dev as default branch
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [ ] 2. Set up core configuration and dependencies
  - Create requirements.txt with fastapi, uvicorn, motor, pydantic, httpx, pyjwt, python-dotenv, colorlog
  - Create .env file with placeholder values for all configuration variables
  - Implement app/core/config.py to load environment variables and export configuration constants
  - Add module docstring with purpose and dependencies
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 3. Implement logging configuration
  - Create app/core/logging_config.py with colored console formatter
  - Configure log levels (DEBUG, INFO, WARNING, ERROR) with color coding
  - Set up formatters with timestamp, log level, module name, function name
  - Create logger instances for different modules (kivi, kivi.ai, kivi.webhook, kivi.db)
  - Add setup_logging() function to initialize logging at app startup
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ] 4. Create database connection layer with mock data support
  - Implement app/db/mongodb.py with Motor async client
  - Create connect_db() and close_db() functions for lifecycle management
  - Implement get_db() function that returns MockDatabase when USE_MOCK_DATA=true
  - Create MockDatabase class with in-memory collections (users, transactions, message_logs, notifications, user_rules)
  - Implement collection-like interface for MockDatabase matching MongoDB API
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 20.8, 20.9_

- [ ] 5. Implement security and authentication modules
  - Create app/core/security.py with JWT token functions
  - Implement create_token(user_id, phone) function using PyJWT
  - Implement verify_token(token) function with expiration checking
  - Create get_current_user() FastAPI dependency for protected endpoints
  - Implement app/utils/jwt_handler.py with encode_jwt() and decode_jwt() wrapper functions
  - Create app/core/exceptions.py with custom exception classes
  - _Requirements: 5.2, 5.3, 5.4, 14.5_

- [ ] 6. Create utility modules
  - Implement app/utils/helpers.py with format_currency(), safe_get(), generate_id()
  - Implement app/utils/date_utils.py with now_iso(), parse_date(), get_week_range(), get_month_range()
  - Implement app/utils/http_client.py with async make_request() function including retry logic
  - Add module docstrings with purpose, dependencies, and example usage
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [ ] 7. Implement user data model with gig worker profile
  - Create app/models/user_model.py with UserProfile Pydantic model
  - Include fields for gig_platforms, financial_summary with income_volatility, income_sources
  - Implement get_user_by_phone(db, phone) async function
  - Implement upsert_user(db, user_dict) async function
  - Implement create_sample_user(phone) function with gig worker sample data (delivery partner profile)
  - Add support for both mock data and MongoDB operations
  - _Requirements: 6.3, 6.4, 6.5, 19.1, 19.2, 19.3, 20.1_

- [ ] 8. Implement transaction data model
  - Create app/models/transaction_model.py with Transaction Pydantic model
  - Include fields for transaction_id, user_id, amount, vendor, category, transaction_type, timestamp, source, raw_sms_text
  - Implement get_transactions(db, user_id, start_date, end_date, category) async function
  - Implement create_transaction(db, txn) async function
  - Add compound index support for user_id + timestamp queries
  - _Requirements: 7.5, 7.6, 20.2, 20.7_

- [ ] 9. Implement message log data model
  - Create app/models/message_log_model.py with MessageLog Pydantic model
  - Implement create_message_doc(user_id, phone, metadata, role, text, model) function
  - Implement save_message(db, message_doc) async function with error handling
  - Implement get_conversation_history(db, user_id, limit) async function
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 20.3_

- [ ] 10. Implement session model for JWT refresh tokens
  - Create app/models/session_model.py with Session Pydantic model
  - Implement create_session(db, user_id, refresh_token) async function
  - Implement get_session(db, session_id) async function
  - _Requirements: 5.1, 5.2_

- [ ] 11. Implement SMS parser service
  - Create app/services/sms_parser.py with parse_sms(text) function
  - Use regex patterns to extract amount, vendor, timestamp, transaction_type (debit/credit)
  - Handle multiple SMS formats from different banks
  - Return structured dictionary with extracted fields
  - Add inline comments explaining regex patterns
  - _Requirements: 7.2_

- [ ] 12. Implement expense analyzer service
  - Create app/services/expense_analyzer.py with categorize_transaction(txn) function
  - Implement keyword matching for categories: food, transport, shopping, bills, entertainment, healthcare, education, others
  - Implement summarize_transactions(transactions) function returning category totals
  - Add gig-worker specific categories (fuel, bike maintenance, platform fees)
  - _Requirements: 7.3, 7.4, 9.1, 9.2, 9.3_

- [ ] 13. Implement nudge engine with gig worker insights
  - Create app/services/nudge_engine.py with generate_nudges(user, transactions) function
  - Implement rule-based logic for low_balance, budget_exceeded, unusual_spending, savings_goal_progress
  - Implement generate_gig_worker_insights(user, transactions) function
  - Add income pattern analysis, platform comparison, emergency fund runway calculations
  - Implement evaluate_rules(db, user_id, transaction) async function
  - _Requirements: 9.4, 9.5, 21.1, 21.2, 21.3, 21.4, 21.5_

- [ ] 14. Implement AI provider modules
  - Create app/services/ai_providers/openai_provider.py with call_openai(prompt) async function
  - Create app/services/ai_providers/anthropic_provider.py with call_anthropic(prompt) async function
  - Return mocked responses when API keys not configured
  - Include commented sample code showing real API integration
  - Add error handling and logging for API calls
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 15. Implement AI chat service
  - Create app/services/ai_chat.py with chat_with_model(metadata, message, provider) async function
  - Build prompt with serialized user metadata (name, job, gig_platforms, goals, transaction_summary)
  - Route to appropriate AI provider based on provider parameter
  - Log prompt at DEBUG level and response at INFO level with latency
  - Return dictionary with reply, provider, usage fields
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.5_

- [ ] 16. Implement WhatsApp service
  - Create app/services/whatsapp_service.py with handle_incoming_webhook(db, payload) async function
  - Validate webhook signature/token
  - Extract phone, user_id, message from Meta webhook payload
  - Get user profile to build metadata context
  - Persist user message using message_log_model
  - Call chat_with_model() to get AI response
  - Persist bot message
  - Send reply via send_whatsapp_text()
  - Implement send_whatsapp_text(phone, text) async function
  - POST to Meta Graph API with WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID
  - Add error handling and logging for API failures
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.2, 8.3, 8.4, 8.5_

- [ ] 17. Implement Account Aggregator service placeholder
  - Create app/services/aa_service.py with fetch_aa_data(user_id) async function
  - Return sample gig worker financial data (multiple income sources, transactions)
  - Implement normalize_aa_data(raw_data) function to transform to internal format
  - Add comments indicating future real AA API integration
  - _Requirements: 19.2, 19.3_

- [ ] 18. Implement authentication routes
  - Create app/api/v1/routes_auth.py with POST /login endpoint
  - Accept phone and password in request body
  - Validate credentials (use mock validation for now)
  - Generate JWT token using create_token()
  - Return access_token and token_type in response
  - Add module docstring with endpoint documentation
  - _Requirements: 5.1, 5.2_

- [ ] 19. Implement user profile routes
  - Create app/api/v1/routes_user.py with GET /users/me endpoint
  - Use get_current_user dependency for authentication
  - Return authenticated user profile from database
  - Implement PUT /users/me endpoint for profile updates
  - Validate request body with Pydantic model
  - Update user profile in database
  - _Requirements: 6.1, 6.2, 6.5_

- [ ] 20. Implement finance routes
  - Create app/api/v1/routes_finance.py with GET /transactions endpoint
  - Support query parameters for start_date, end_date, category filtering
  - Implement POST /transactions endpoint for manual entries
  - Implement POST /transactions/sms endpoint
  - Parse SMS text using sms_parser
  - Classify transaction using expense_analyzer
  - Create transaction record with source="sms"
  - Evaluate rules using nudge_engine
  - Implement GET /dashboard endpoint with balance, monthly_spending, category_breakdown, budgets
  - Implement GET /reports/weekly and GET /reports/monthly endpoints
  - Use MongoDB aggregation pipelines or in-memory calculations for reports
  - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6, 7.7, 7.8, 22.1, 22.2, 22.3, 22.4_

- [ ] 21. Implement WhatsApp webhook routes
  - Create app/api/v1/routes_whatsapp.py with POST /webhook endpoint
  - Call handle_incoming_webhook(db, payload) from whatsapp_service
  - Return 200 OK quickly for webhook acknowledgment
  - Implement POST /send_notification endpoint
  - Accept phone, text, provider in request body
  - Call send_whatsapp_text() to send message
  - Persist outbound message to database with role="bot"
  - _Requirements: 1.1, 1.5, 8.1, 8.2, 8.4_

- [ ] 22. Implement AI chat routes for mobile app
  - Create app/api/v1/routes_ai.py with POST /chat endpoint
  - Accept user_id, phone, metadata, message, provider in request body
  - Call chat_with_model() with provided parameters
  - Save user message using message_log_model
  - Save bot message using message_log_model
  - Return AI response in HTTP response body
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 23. Implement user onboarding flow
  - Add onboarding logic to POST /login endpoint for first-time users
  - Create user profile with create_sample_user() including gig worker data
  - Populate sample Account Aggregator data with multiple income sources
  - Store financial data in user metadata
  - Send welcome WhatsApp message using send_whatsapp_text()
  - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6_

- [ ] 24. Create FastAPI application and wire routes
  - Create app/main.py with FastAPI app initialization
  - Import and include all route modules (auth, user, finance, whatsapp, ai)
  - Add startup event handler to call connect_db() and setup_logging()
  - Add shutdown event handler to call close_db()
  - Create root GET / endpoint returning project name and brief reference
  - Configure CORS for mobile app domain
  - Add global exception handler
  - _Requirements: 12.3, 12.4_

- [ ] 25. Create API documentation
  - Create docs/ directory
  - Create docs/API_ENDPOINTS.md with complete endpoint documentation
  - Document all endpoints with HTTP method, path, description, request/response schemas
  - Provide working curl command examples for each endpoint
  - Include authentication headers for protected endpoints
  - Organize by route module (auth, user, finance, whatsapp, ai)
  - Create docs/samples/ directory with sample JSON files
  - Create sample_user.json with gig worker profile
  - Create sample_transactions.json with gig platform earnings
  - Create sample_sms_messages.json with payment notifications
  - Create sample_webhook_payload.json with WhatsApp conversation
  - Create sample_gig_worker_scenarios.json with various personas
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

- [ ] 26. Create project README and documentation
  - Create README.md with project overview for KIVI hackathon project
  - Add setup instructions (install dependencies, configure .env, run uvicorn)
  - Add section on gig worker target audience
  - Document Git branching strategy (prod, uat, dev, feature branches)
  - Add quick start guide with sample curl commands
  - Document mock data vs MongoDB configuration
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_




## Git Workflow Instructions

For each task above:
1. Create a new feature branch from dev: `git checkout dev && git checkout -b feature/task-{number}-{short-name}`
2. Implement the task
3. Commit changes with clear message: `git commit -m "feat: {task description}"`
4. Push feature branch: `git push origin feature/task-{number}-{short-name}`
5. Merge into dev: `git checkout dev && git merge feature/task-{number}-{short-name}`
6. Push dev: `git push origin dev`

Example for Task 2:
```bash
git checkout dev
git checkout -b feature/task-2-core-config
# ... implement task ...
git add .
git commit -m "feat: set up core configuration and dependencies"
git push origin feature/task-2-core-config
git checkout dev
git merge feature/task-2-core-config
git push origin dev
```

_Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_
