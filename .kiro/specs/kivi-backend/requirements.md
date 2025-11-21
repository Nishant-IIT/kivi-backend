# Requirements Document

## Introduction

KIVI Backend is a FastAPI-based system for the KIVI hackathon project that integrates WhatsApp messaging, AI chat capabilities, financial transaction tracking, and user profile management. The system processes incoming WhatsApp messages through Meta's Cloud API, responds using AI providers (OpenAI or Anthropic), and maintains comprehensive message logs and transaction data in MongoDB. The architecture follows a functional programming style with modular AI provider support.

## Glossary

- **KIVI_System**: The FastAPI backend application that handles WhatsApp webhooks, AI chat, and financial data
- **Meta_WhatsApp_API**: Meta's Cloud API for sending and receiving WhatsApp messages
- **AI_Provider**: A pluggable module that interfaces with AI services (OpenAI or Anthropic)
- **Message_Log**: A MongoDB document storing chat messages with metadata, role, and timestamps
- **User_Metadata**: A dictionary containing user profile information (name, job, goals, transaction summary)
- **Transaction**: A financial transaction record with amount, vendor, category, and timestamp
- **Chat_Function**: The single-use function for conversational AI responses only
- **JWT_Token**: JSON Web Token used for authentication without OTP
- **Webhook_Payload**: JSON data received from Meta WhatsApp Cloud API

## Requirements

### Requirement 1

**User Story:** As a WhatsApp user, I want to send messages to the KIVI bot, so that I can receive AI-powered financial guidance

#### Acceptance Criteria

1. WHEN the Meta_WhatsApp_API sends a webhook POST request, THE KIVI_System SHALL validate the webhook signature or token
2. WHEN a valid webhook is received, THE KIVI_System SHALL extract the phone number, user identifier, and message text from the payload
3. WHEN message data is extracted, THE KIVI_System SHALL persist the user message to MongoDB with fields user_id, phone, metadata, role "user", text, model, and timestamp
4. WHEN the user message is persisted, THE KIVI_System SHALL invoke the chat_with_model function with user metadata and message text
5. WHEN the AI response is received, THE KIVI_System SHALL persist the bot reply to MongoDB with role "bot" and send the reply via Meta_WhatsApp_API

### Requirement 2

**User Story:** As a system administrator, I want the AI chat to use user context and serve multiple channels, so that responses are personalized and accessible via WhatsApp and mobile app

#### Acceptance Criteria

1. THE KIVI_System SHALL provide a function chat_with_model that accepts metadata dictionary, message string, and provider string with default "openai"
2. WHEN chat_with_model is invoked, THE KIVI_System SHALL build a prompt containing serialized user metadata including name, job, goals, and recent transaction summary
3. WHEN the prompt is built, THE KIVI_System SHALL route the request to the specified AI_Provider wrapper function
4. WHEN the AI_Provider returns a response, THE KIVI_System SHALL log both the prompt and response using the logging configuration
5. WHEN logging is complete, THE KIVI_System SHALL return a dictionary containing reply text, provider name, and usage placeholder
6. THE KIVI_System SHALL use the same chat_with_model function for both WhatsApp webhook messages and mobile app chat UI requests

### Requirement 3

**User Story:** As a developer, I want to swap AI providers easily, so that I can choose between OpenAI and Anthropic without code changes

#### Acceptance Criteria

1. THE KIVI_System SHALL implement separate provider modules for openai_provider and anthropic_provider
2. THE KIVI_System SHALL define identical function signatures call_openai and call_anthropic that accept prompt string and return response string
3. WHEN a provider function is called without valid API keys, THE KIVI_System SHALL return a mocked response indicating the provider name and prompt excerpt
4. THE KIVI_System SHALL include commented sample code in each provider module showing real API integration
5. WHEN chat_with_model receives a provider parameter, THE KIVI_System SHALL route to the corresponding provider function by name

### Requirement 4

**User Story:** As a system operator, I want all chat messages logged to MongoDB, so that I can audit conversations and analyze usage

#### Acceptance Criteria

1. THE KIVI_System SHALL define a message log document structure with fields user_id, phone, metadata, role, text, provider, and timestamp
2. THE KIVI_System SHALL provide a function create_message_doc that accepts user_id, phone, metadata, role, text, and model parameters
3. WHEN create_message_doc is called, THE KIVI_System SHALL return a dictionary ready for MongoDB insertion
4. THE KIVI_System SHALL provide an async function save_message that accepts database connection and message document
5. WHEN save_message is invoked, THE KIVI_System SHALL insert the document into the message_logs collection with error handling

### Requirement 5

**User Story:** As a user, I want to authenticate with JWT, so that I can access protected API endpoints securely

#### Acceptance Criteria

1. THE KIVI_System SHALL provide a POST /login endpoint that accepts credentials and returns a JWT token
2. WHEN valid credentials are provided, THE KIVI_System SHALL generate a JWT token using PyJWT with configurable secret and expiration
3. THE KIVI_System SHALL provide functions create_token and verify_token in the security module
4. WHEN a protected endpoint is accessed, THE KIVI_System SHALL verify the JWT token and extract user identity
5. THE KIVI_System SHALL NOT implement OTP-based authentication

### Requirement 6

**User Story:** As a user, I want to manage my profile, so that the AI has accurate context about me

#### Acceptance Criteria

1. THE KIVI_System SHALL provide a GET /users/me endpoint that returns the authenticated user profile
2. THE KIVI_System SHALL provide a PUT /users/me endpoint that accepts profile updates
3. THE KIVI_System SHALL define a Pydantic user model with validation for profile fields
4. THE KIVI_System SHALL provide async functions get_user_by_phone and upsert_user for database operations
5. WHEN a user profile is updated, THE KIVI_System SHALL persist changes to MongoDB with error handling

### Requirement 7

**User Story:** As a mobile app user, I want my SMS transactions automatically processed and categorized, so that I can track spending without manual entry

#### Acceptance Criteria

1. THE KIVI_System SHALL provide a POST /transactions/sms endpoint that accepts SMS message text from the mobile app
2. WHEN an SMS is received, THE KIVI_System SHALL parse the text using parse_sms function to extract amount, vendor, timestamp, and transaction type (debit/credit)
3. WHEN transaction data is extracted, THE KIVI_System SHALL classify the transaction into a category using keyword matching and vendor patterns
4. THE KIVI_System SHALL support categories including food, transport, shopping, bills, entertainment, healthcare, education, and others
5. WHEN classification is complete, THE KIVI_System SHALL create a transaction record with user_id, amount, vendor, category, timestamp, source "sms", and raw_sms_text
6. THE KIVI_System SHALL persist the classified transaction to the transactions collection or mock data store
7. THE KIVI_System SHALL provide a GET /transactions endpoint that returns categorized transaction history for the authenticated user
8. THE KIVI_System SHALL provide a POST /transactions endpoint that accepts manual transaction entries or Account Aggregator data

### Requirement 8

**User Story:** As a system administrator, I want to send proactive WhatsApp notifications, so that I can engage users with timely information

#### Acceptance Criteria

1. THE KIVI_System SHALL provide a POST /send_notification endpoint that accepts phone, text, and provider parameters
2. WHEN send_notification is invoked, THE KIVI_System SHALL call send_whatsapp_text function with phone and text
3. THE KIVI_System SHALL implement send_whatsapp_text to POST to Meta Graph API using WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID
4. WHEN an outbound message is sent, THE KIVI_System SHALL persist the message to MongoDB with role "bot"
5. WHEN the Meta API call fails, THE KIVI_System SHALL log the error and return appropriate HTTP status

### Requirement 9

**User Story:** As a developer, I want transaction categorization and analysis, so that I can provide spending insights

#### Acceptance Criteria

1. THE KIVI_System SHALL provide a function categorize_transaction that accepts a transaction and returns a category string
2. WHEN categorize_transaction is called, THE KIVI_System SHALL use keyword matching on vendor field to determine category
3. THE KIVI_System SHALL provide a function summarize_transactions that accepts transaction list and returns totals per category
4. THE KIVI_System SHALL provide a function generate_nudges that accepts user and transactions and returns nudge strings
5. WHEN generate_nudges is called, THE KIVI_System SHALL apply rule-based logic for low balance and overspending detection

### Requirement 10

**User Story:** As a developer, I want centralized configuration management, so that I can deploy with environment-specific settings

#### Acceptance Criteria

1. THE KIVI_System SHALL load configuration from environment variables using os.getenv
2. THE KIVI_System SHALL provide constants for MONGO_URI, JWT_SECRET, WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, OPENAI_API_KEY, and ANTHROPIC_API_KEY
3. THE KIVI_System SHALL include a .env file with placeholder values for all required configuration
4. THE KIVI_System SHALL include configuration comments referencing the project brief at /mnt/data/MumbaiHacks 2025.pdf
5. THE KIVI_System SHALL export configuration as accessible attributes or dictionary

### Requirement 11

**User Story:** As a system operator, I want comprehensive logging with easy debugging capabilities, so that I can quickly troubleshoot issues and monitor AI interactions

#### Acceptance Criteria

1. THE KIVI_System SHALL configure Python logging with console output, colored formatting, and structured log levels (DEBUG, INFO, WARNING, ERROR)
2. WHEN AI prompts are sent, THE KIVI_System SHALL log the full prompt text, user_id, and timestamp at DEBUG level
3. WHEN AI responses are received, THE KIVI_System SHALL log the response text, provider name, and latency at INFO level
4. WHEN errors occur, THE KIVI_System SHALL log the full exception traceback with context at ERROR level
5. THE KIVI_System SHALL log all incoming webhook requests, outbound API calls, and database operations with request/response details for debugging
6. THE KIVI_System SHALL provide a logging configuration module that sets up formatters with timestamps, log levels, module names, and function names
7. THE KIVI_System SHALL include log statements at key execution points (function entry, API calls, database operations, error conditions)

### Requirement 12

**User Story:** As a developer, I want MongoDB connection management, so that database operations are reliable

#### Acceptance Criteria

1. THE KIVI_System SHALL create an async Motor client for MongoDB connectivity
2. THE KIVI_System SHALL provide a get_db function that returns a Database instance
3. WHEN the FastAPI application starts, THE KIVI_System SHALL initialize the MongoDB client connection
4. WHEN the FastAPI application shuts down, THE KIVI_System SHALL close the MongoDB client connection
5. THE KIVI_System SHALL include try-except blocks for all database operations with error logging

### Requirement 13

**User Story:** As a mobile app user, I want to chat with the AI through the app interface, so that I can get financial guidance without using WhatsApp

#### Acceptance Criteria

1. THE KIVI_System SHALL provide a POST /chat endpoint in the AI routes module for mobile app chat UI
2. WHEN POST /chat is invoked, THE KIVI_System SHALL accept user_id, phone, metadata, message, and provider parameters
3. WHEN the request is received, THE KIVI_System SHALL call chat_with_model with provided parameters (same function used by WhatsApp)
4. WHEN chat_with_model returns, THE KIVI_System SHALL save both user and bot messages using message_log_model
5. WHEN messages are saved, THE KIVI_System SHALL return the AI response in the HTTP response body for display in mobile app

### Requirement 14

**User Story:** As a developer, I want utility functions for common operations, so that I can write cleaner code

#### Acceptance Criteria

1. THE KIVI_System SHALL provide a format_currency function that formats numeric amounts with currency symbol
2. THE KIVI_System SHALL provide a safe_get function that retrieves dictionary values with default fallback
3. THE KIVI_System SHALL provide a now_iso function that returns current timestamp in ISO 8601 format
4. THE KIVI_System SHALL provide an async HTTP client wrapper using httpx with retry logic
5. THE KIVI_System SHALL provide JWT handler functions wrapping PyJWT for token operations

### Requirement 15

**User Story:** As a new developer, I want clear documentation, so that I can understand and extend the codebase

#### Acceptance Criteria

1. THE KIVI_System SHALL include a module-level docstring at the top of each Python file describing its purpose
2. THE KIVI_System SHALL include dependency information in each file's docstring
3. THE KIVI_System SHALL include example usage in each file's docstring where applicable
4. THE KIVI_System SHALL provide a README.md with setup instructions and reference to the project brief
5. THE KIVI_System SHALL include inline comments explaining complex logic and data flow

### Requirement 16

**User Story:** As a developer, I want the project initialized as a Git repository with proper branching strategy, so that I can follow best practices for development workflow

#### Acceptance Criteria

1. THE KIVI_System SHALL be initialized as a Git repository with git init
2. THE KIVI_System SHALL include a .gitignore file that excludes .env, __pycache__, .pyc files, and venv directories
3. THE KIVI_System SHALL be connected to a GitHub remote repository
4. WHEN the remote is configured, THE KIVI_System SHALL create three branches: prod, uat, and dev
5. WHEN branches are created, THE KIVI_System SHALL push all branches to GitHub with dev as the default development branch

### Requirement 17

**User Story:** As a developer, I want to follow Git branching best practices, so that development is organized and traceable

#### Acceptance Criteria

1. WHEN a new task is started, THE KIVI_System development SHALL create a feature branch from dev with descriptive naming
2. WHEN a task is completed, THE KIVI_System changes SHALL be committed to the feature branch with clear commit messages
3. WHEN commits are ready, THE KIVI_System SHALL push the feature branch to GitHub
4. WHEN the feature is validated, THE KIVI_System changes SHALL be merged into the dev branch
5. THE KIVI_System SHALL maintain dev branch as the primary development branch with prod and uat for staging and production

### Requirement 18

**User Story:** As a developer, I want comprehensive API documentation with curl examples, so that I can easily test and integrate with endpoints

#### Acceptance Criteria

1. THE KIVI_System SHALL include a docs/ directory at the project root for all documentation files
2. THE KIVI_System SHALL provide an API_ENDPOINTS.md file in the docs/ directory documenting all REST endpoints
3. WHEN an endpoint is documented, THE KIVI_System SHALL include the HTTP method, path, description, request body schema, and response schema
4. WHEN an endpoint is documented, THE KIVI_System SHALL provide a working curl command example with sample request data
5. THE KIVI_System SHALL include authentication requirements and header examples for protected endpoints in the documentation
6. THE KIVI_System SHALL organize endpoint documentation by route module (auth, user, finance, whatsapp, ai)

### Requirement 19

**User Story:** As a new user, I want an automated onboarding flow with sample financial data, so that I can start using the AI chat immediately

#### Acceptance Criteria

1. WHEN a user logs in through the app for the first time, THE KIVI_System SHALL create a user profile with phone number and basic information
2. WHEN the profile is created, THE KIVI_System SHALL populate the user profile with sample Account Aggregator data including transactions, budgets, and financial goals
3. WHEN sample data is populated, THE KIVI_System SHALL store the financial data as part of the user metadata to serve as persona context for AI interactions
4. WHEN the user account is fully created, THE KIVI_System SHALL send a welcome message to the user's WhatsApp number via send_whatsapp_text
5. WHEN the user sends a chat message, THE KIVI_System SHALL include the user profile metadata (name, job, goals, transaction summary) as context in the AI prompt
6. THE KIVI_System SHALL ensure the AI provider receives complete user context to provide accurate and personalized responses

### Requirement 20

**User Story:** As a system architect, I want an intelligent MongoDB schema design with initial mock data support, so that I can develop features before full database integration

#### Acceptance Criteria

1. THE KIVI_System SHALL define a users collection schema with embedded documents for profile, financial_summary, budgets, goals, and notification_preferences
2. THE KIVI_System SHALL define a transactions collection schema with indexed fields for user_id, timestamp, category, amount, and vendor for efficient querying
3. THE KIVI_System SHALL define a message_logs collection schema with indexed fields for user_id, timestamp, and role for conversation history retrieval
4. THE KIVI_System SHALL define a notifications collection schema with fields for user_id, trigger_type, rule_id, message, status, and timestamp for tracking sent notifications
5. THE KIVI_System SHALL define a user_rules collection schema with fields for user_id, rule_type, conditions, threshold_values, and active status for rule engine configuration
6. THE KIVI_System SHALL include aggregation-friendly fields in transactions schema (daily_total, weekly_total, monthly_total, category_totals) for dashboard queries
7. THE KIVI_System SHALL use compound indexes on user_id + timestamp for time-range queries in transactions and message_logs collections
8. WHEN MongoDB is not yet configured, THE KIVI_System SHALL use in-memory mock data structures that match the defined schemas
9. THE KIVI_System SHALL provide data access functions that work with both mock data and MongoDB with identical interfaces for seamless migration

### Requirement 21

**User Story:** As a user, I want to receive automated notifications based on spending patterns, so that I can stay informed about my financial health

#### Acceptance Criteria

1. THE KIVI_System SHALL provide a rule engine that evaluates user-defined rules against transaction data
2. WHEN a transaction is created, THE KIVI_System SHALL check active rules for the user and evaluate trigger conditions
3. WHEN a rule condition is met, THE KIVI_System SHALL create a notification record and send a WhatsApp message to the user
4. THE KIVI_System SHALL support rule types including budget_exceeded, low_balance, unusual_spending, and savings_goal_progress
5. THE KIVI_System SHALL store rule evaluation results in the notifications collection with trigger details and timestamp

### Requirement 22

**User Story:** As a user, I want to view dashboard and periodic reports, so that I can understand my spending patterns

#### Acceptance Criteria

1. THE KIVI_System SHALL provide a GET /dashboard endpoint that returns current balance, monthly spending, category breakdown, and active budgets
2. THE KIVI_System SHALL provide a GET /reports/weekly endpoint that returns spending summary, top categories, and comparison to previous week
3. THE KIVI_System SHALL provide a GET /reports/monthly endpoint that returns monthly spending summary, category trends, and budget adherence
4. WHEN a report endpoint is called, THE KIVI_System SHALL use MongoDB aggregation pipelines to compute totals, averages, and category breakdowns
5. THE KIVI_System SHALL cache report data with 1-hour TTL to optimize performance for frequently accessed reports
