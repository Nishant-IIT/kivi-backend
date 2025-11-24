# KIVI Backend - Standard Response Format

## Overview

All API endpoints in the KIVI Backend return responses in a standardized format to ensure consistency and ease of integration.

## Response Structure

### Success Response

```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "Operation completed successfully",
  "data": {
    // Response data here
  },
  "error": null
}
```

### Error Response

```json
{
  "success": false,
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "data": null,
  "error": {
    "type": "ErrorType",
    "details": "Additional error details (optional)"
  }
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indicates whether the request was successful |
| `code` | string | Response code (see codes below) |
| `message` | string | Human-readable message describing the result |
| `data` | object/null | Response data (null on error) |
| `error` | object/null | Error details (null on success) |

### Error Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Type of error (e.g., "ValidationError", "DatabaseError") |
| `details` | string/null | Additional error details (may be null in production) |

## Response Codes

### Success Codes (2xx)

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `SUCCESS` | Operation completed successfully | 200 |
| `CREATED` | Resource created successfully | 201 |
| `UPDATED` | Resource updated successfully | 200 |
| `DELETED` | Resource deleted successfully | 200 |

### Client Error Codes (4xx)

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `BAD_REQUEST` | Invalid request format or parameters | 400 |
| `UNAUTHORIZED` | Authentication required | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `CONFLICT` | Resource conflict (e.g., duplicate) | 409 |
| `VALIDATION_ERROR` | Request validation failed | 422 |
| `INVALID_CREDENTIALS` | Invalid username or password | 401 |
| `TOKEN_EXPIRED` | JWT token has expired | 401 |
| `TOKEN_INVALID` | JWT token is invalid | 401 |

### Server Error Codes (5xx)

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INTERNAL_ERROR` | Unexpected server error | 500 |
| `DATABASE_ERROR` | Database operation failed | 500 |
| `EXTERNAL_SERVICE_ERROR` | External service unavailable | 500 |
| `AI_SERVICE_ERROR` | AI provider error | 500 |
| `WHATSAPP_SERVICE_ERROR` | WhatsApp API error | 500 |

## Examples

### Example 1: Successful Login

**Request:**
```bash
POST /api/v1/login
Content-Type: application/json

{
  "phone": "+919876543210",
  "password": "mypassword"
}
```

**Response:**
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": "usr_9876543210",
    "phone": "+919876543210"
  },
  "error": null
}
```

### Example 2: Invalid Credentials

**Request:**
```bash
POST /api/v1/login
Content-Type: application/json

{
  "phone": "+919876543210",
  "password": "wrongpassword"
}
```

**Response:**
```json
{
  "success": false,
  "code": "INVALID_CREDENTIALS",
  "message": "Invalid phone number or password",
  "data": null,
  "error": {
    "type": "AuthenticationError",
    "details": "Please check your credentials and try again"
  }
}
```

### Example 3: Get User Profile (Success)

**Request:**
```bash
GET /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "User profile retrieved successfully",
  "data": {
    "user_id": "usr_9876543210",
    "phone": "+919876543210",
    "name": "John Doe",
    "email": "john@example.com",
    "job": "Delivery Partner",
    "city": "Mumbai",
    "gig_platforms": ["Swiggy", "Zomato"],
    "financial_summary": {
      "current_balance": 12000.0,
      "avg_monthly_income": 28000.0,
      "monthly_expenses": 22000.0
    },
    "budgets": [],
    "goals": [],
    "notification_preferences": {
      "whatsapp_enabled": true,
      "budget_alerts": true
    },
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:22:00Z"
  },
  "error": null
}
```

### Example 4: User Not Found

**Request:**
```bash
GET /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": false,
  "code": "NOT_FOUND",
  "message": "User profile not found",
  "data": null,
  "error": {
    "type": "NotFoundError",
    "details": "No profile found for user usr_9876543210"
  }
}
```

### Example 5: Update User Profile (Success)

**Request:**
```bash
PUT /api/v1/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "John Smith",
  "city": "Delhi"
}
```

**Response:**
```json
{
  "success": true,
  "code": "UPDATED",
  "message": "User profile updated successfully",
  "data": {
    "user_id": "usr_9876543210",
    "phone": "+919876543210",
    "name": "John Smith",
    "city": "Delhi",
    // ... other fields
  },
  "error": null
}
```

### Example 6: Internal Server Error

**Request:**
```bash
GET /api/v1/some-endpoint
```

**Response:**
```json
{
  "success": false,
  "code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "data": null,
  "error": {
    "type": "InternalError",
    "details": null
  }
}
```

## Client Integration Guidelines

### Checking Response Success

Always check the `success` field first:

```javascript
// JavaScript example
const response = await fetch('/api/v1/users/me');
const result = await response.json();

if (result.success) {
  // Handle success
  console.log('Data:', result.data);
  console.log('Message:', result.message);
} else {
  // Handle error
  console.error('Error:', result.message);
  console.error('Code:', result.code);
  console.error('Details:', result.error);
}
```

```python
# Python example
import requests

response = requests.get('http://localhost:8000/api/v1/users/me')
result = response.json()

if result['success']:
    # Handle success
    print('Data:', result['data'])
    print('Message:', result['message'])
else:
    # Handle error
    print('Error:', result['message'])
    print('Code:', result['code'])
    print('Details:', result['error'])
```

### Error Handling by Code

```javascript
// JavaScript example
if (!result.success) {
  switch (result.code) {
    case 'INVALID_CREDENTIALS':
      // Show login error
      showError('Invalid username or password');
      break;
    case 'TOKEN_EXPIRED':
      // Redirect to login
      redirectToLogin();
      break;
    case 'NOT_FOUND':
      // Show not found message
      showError('Resource not found');
      break;
    case 'DATABASE_ERROR':
    case 'INTERNAL_ERROR':
      // Show generic error
      showError('Something went wrong. Please try again later.');
      break;
    default:
      showError(result.message);
  }
}
```

## Benefits

1. **Consistency**: All endpoints follow the same structure
2. **Easy Error Handling**: Clients can handle errors uniformly
3. **Machine Readable**: Error codes enable programmatic error handling
4. **Human Readable**: Messages provide context for users
5. **Debugging**: Error details help with troubleshooting (in development)
6. **Type Safety**: Predictable structure enables strong typing in clients

## Migration Notes

All endpoints have been updated to use this standard format. If you're integrating with the API:

1. Always check the `success` field
2. Use `code` for programmatic error handling
3. Display `message` to users
4. Access response data from the `data` field
5. Check `error.details` for additional debugging information
