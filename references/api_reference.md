# Epsimo API Reference

Complete reference for the Epsimo Agent Platform API v1.0

**Base URL:** `https://api.epsimoagents.com`

---

## Table of Contents

1. [Authentication](#authentication)
2. [HTTP Status Codes](#http-status-codes)
3. [Error Handling](#error-handling)
4. [Rate Limits](#rate-limits)
5. [Projects](#projects)
6. [Assistants](#assistants)
7. [Threads](#threads)
8. [Messages](#messages)
9. [Files](#files)
10. [Credits & Billing](#credits--billing)
11. [Virtual Database](#virtual-database)

---

## Authentication

All API requests require authentication using JWT tokens.

### POST /auth/signup

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure-password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "email": "user@example.com",
    "user_id": "usr_..."
  }
}
```

### POST /auth/login

Authenticate and receive access token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure-password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbG...",
  "token": "eyJhbG...",
  "jwt_token": "eyJhbG...",
  "expires_in": 3600
}
```

**Error Response (401):**
```json
{
  "error": "Invalid credentials",
  "detail": "Email or password is incorrect"
}
```

### GET /auth/thread-info

Get current user information and thread usage.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "email": "user@example.com",
  "user_id": "usr_123",
  "thread_counter": 45,
  "thread_max": 100,
  "subscription_tier": "standard"
}
```

### Token Refresh

Tokens expire after 1 hour. To refresh:

```python
# Python example
import requests

def refresh_token(expired_token):
    # Re-authenticate with stored credentials
    response = requests.post(
        "https://api.epsimoagents.com/auth/login",
        json={"email": stored_email, "password": stored_password}
    )
    return response.json()["access_token"]
```

---

## HTTP Status Codes

| Code | Meaning | Common Causes | Recommended Action |
|------|---------|---------------|-------------------|
| 200 | Success | Request completed successfully | Continue processing |
| 201 | Created | Resource created successfully | Capture returned ID |
| 204 | No Content | Deletion succeeded | Confirm success |
| 400 | Bad Request | Invalid payload, missing fields | Validate request schema |
| 401 | Unauthorized | Invalid/expired token | Refresh or re-authenticate |
| 403 | Forbidden | Insufficient permissions | Check user/project access |
| 404 | Not Found | Resource doesn't exist | Verify ID is correct |
| 409 | Conflict | Duplicate resource | Check for existing records |
| 422 | Validation Error | Schema validation failed | Review error details |
| 429 | Too Many Requests | Rate limit exceeded | Implement exponential backoff |
| 500 | Server Error | Backend issue | Retry with exponential backoff |
| 503 | Service Unavailable | Temporary downtime | Wait and retry |

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "field": "problematic_field_name",
  "code": "ERROR_CODE"
}
```

### Example Error Responses

**Validation Error (422):**
```json
{
  "error": "Validation Error",
  "detail": "Field 'name' is required",
  "field": "name"
}
```

**Authentication Error (401):**
```json
{
  "error": "Unauthorized",
  "detail": "Token has expired or is invalid",
  "code": "TOKEN_EXPIRED"
}
```

### Retry Logic with Exponential Backoff

```python
import time
import requests
from requests.exceptions import HTTPError

def make_request_with_retry(url, headers, method="GET", json_data=None, max_retries=5):
    """Make API request with automatic retry on rate limits and server errors."""
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, headers=headers, json=json_data)
            response.raise_for_status()
            return response.json() if response.content else None

        except HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited - exponential backoff
                wait_time = min(60 * (2 ** attempt), 300)  # Max 5 minutes
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            elif e.response.status_code >= 500:
                # Server error - retry with backoff
                wait_time = min(10 * (2 ** attempt), 60)  # Max 1 minute
                print(f"Server error. Waiting {wait_time}s...")
                time.sleep(wait_time)
            elif e.response.status_code == 401:
                # Token expired - try to refresh
                print("Token expired. Attempting refresh...")
                raise
            else:
                # Other errors - don't retry
                raise

    raise Exception(f"Max retries ({max_retries}) exceeded")
```

---

## Rate Limits

| Tier | Limit |
|------|-------|
| Free | 60 requests/minute |
| Standard | 300 requests/minute |
| Premium | 1,000 requests/minute |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 245
X-RateLimit-Reset: 1672531200
```

When rate limited (429), wait and retry with exponential backoff (see [Error Handling](#error-handling)).

---

## Projects

Projects are top-level containers for assistants, threads, and files.

### GET /projects/

List all projects for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
[
  {
    "project_id": "proj_abc123",
    "name": "My AI Project",
    "description": "Customer support automation",
    "created_at": "2024-01-15T10:30:00Z",
    "access_token": "proj_token_..."
  }
]
```

### POST /projects/

Create a new project.

**Request:**
```json
{
  "name": "My New Project",
  "description": "Optional description",
  "metadata": {
    "custom_field": "value"
  }
}
```

**Response (201):**
```json
{
  "project_id": "proj_xyz789",
  "name": "My New Project",
  "description": "Optional description",
  "access_token": "proj_token_...",
  "created_at": "2024-01-15T11:00:00Z"
}
```

### GET /projects/{project_id}

Get project details including project-specific access token.

**Response (200):**
```json
{
  "project_id": "proj_abc123",
  "name": "My AI Project",
  "description": "Customer support automation",
  "access_token": "proj_token_...",
  "token": "proj_token_...",
  "jwt_token": "proj_token_...",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Note:** Use the `access_token` from this response for project-scoped operations (assistants, threads, files).

### DELETE /projects/{project_id}?confirm=true

Delete a project and all associated resources.

**Query Parameters:**
- `confirm=true` (required) - Confirmation flag

**Response (204):**
No content (successful deletion)

---

## Assistants

Assistants are AI agents with specific instructions and capabilities.

### GET /assistants/

List all assistants in a project.

**Headers:**
```
Authorization: Bearer <project_access_token>
```

**Response (200):**
```json
[
  {
    "assistant_id": "asst_abc123",
    "name": "Support Agent",
    "config": {
      "instructions": "You are a helpful support agent",
      "model": "gpt-4o",
      "configurable": {
        "type": "agent",
        "agent_type": "agent"
      }
    },
    "public": false,
    "created_at": "2024-01-15T10:45:00Z"
  }
]
```

### POST /assistants/

Create a new assistant.

**Request:**
```json
{
  "name": "Research Assistant",
  "config": {
    "instructions": "You help with research tasks",
    "model": "gpt-4o",
    "configurable": {
      "type": "agent",
      "agent_type": "agent"
    },
    "tools": [
      {
        "type": "search_tavily",
        "max_results": 5
      },
      {
        "type": "function",
        "name": "update_database",
        "description": "Save structured data",
        "parameters": {
          "type": "object",
          "properties": {
            "key": {"type": "string"},
            "value": {"type": "object"}
          },
          "required": ["key", "value"]
        }
      }
    ]
  },
  "public": false
}
```

**Response (201):**
```json
{
  "assistant_id": "asst_xyz789",
  "name": "Research Assistant",
  "config": { ... },
  "public": false,
  "created_at": "2024-01-15T11:15:00Z"
}
```

### GET /assistants/{assistant_id}

Get assistant details.

**Response (200):**
```json
{
  "assistant_id": "asst_abc123",
  "name": "Support Agent",
  "config": { ... },
  "public": false,
  "created_at": "2024-01-15T10:45:00Z"
}
```

### DELETE /assistants/{assistant_id}

Delete an assistant.

**Response (204):**
No content (successful deletion)

---

## Threads

Threads represent persistent conversation contexts with Virtual Database state.

### GET /threads/

List all threads in a project.

**Headers:**
```
Authorization: Bearer <project_access_token>
```

**Response (200):**
```json
[
  {
    "thread_id": "thread_abc123",
    "name": "Customer #1234",
    "assistant_id": "asst_xyz789",
    "metadata": {
      "configurable": {},
      "type": "thread"
    },
    "created_at": "2024-01-15T12:00:00Z"
  }
]
```

### POST /threads/

Create a new thread.

**Request:**
```json
{
  "name": "Customer Support Session",
  "assistant_id": "asst_xyz789",
  "metadata": {
    "configurable": {},
    "type": "thread"
  },
  "configurable": {
    "type": "agent"
  }
}
```

**Response (201):**
```json
{
  "thread_id": "thread_new123",
  "name": "Customer Support Session",
  "assistant_id": "asst_xyz789",
  "created_at": "2024-01-15T12:30:00Z"
}
```

### GET /threads/{thread_id}

Get thread details and messages.

**Response (200):**
```json
{
  "thread_id": "thread_abc123",
  "name": "Customer #1234",
  "assistant_id": "asst_xyz789",
  "messages": [
    {
      "role": "user",
      "content": "Hello!",
      "timestamp": "2024-01-15T12:01:00Z"
    },
    {
      "role": "assistant",
      "content": "How can I help you?",
      "timestamp": "2024-01-15T12:01:05Z"
    }
  ]
}
```

### POST /threads/{thread_id}/run

Send a message and stream the assistant's response.

**Request:**
```json
{
  "message": "What's the status of my order?",
  "stream": true
}
```

**Response (Streaming):**
```
data: {"type": "start", "run_id": "run_123"}

data: {"type": "content", "delta": "Your"}

data: {"type": "content", "delta": " order"}

data: {"type": "tool_call", "name": "database_query", "args": {...}}

data: {"type": "done"}
```

### DELETE /threads/{thread_id}

Delete a thread.

**Response (204):**
No content (successful deletion)

---

## Messages

### GET /threads/{thread_id}/messages

Get all messages in a thread.

**Query Parameters:**
- `limit` (optional): Max messages to return (default: 50)
- `before` (optional): Cursor for pagination

**Response (200):**
```json
{
  "messages": [
    {
      "message_id": "msg_123",
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-01-15T12:00:00Z"
    }
  ],
  "has_more": false
}
```

### POST /threads/{thread_id}/messages

Add a message to a thread (without triggering assistant).

**Request:**
```json
{
  "role": "user",
  "content": "This is a manual message"
}
```

**Response (201):**
```json
{
  "message_id": "msg_new456",
  "role": "user",
  "content": "This is a manual message",
  "timestamp": "2024-01-15T12:45:00Z"
}
```

---

## Files

### GET /files/

List all files in a project.

**Headers:**
```
Authorization: Bearer <project_access_token>
```

**Response (200):**
```json
[
  {
    "file_id": "file_abc123",
    "filename": "document.pdf",
    "size": 1024567,
    "mime_type": "application/pdf",
    "uploaded_at": "2024-01-15T13:00:00Z"
  }
]
```

### POST /files/

Upload a file.

**Request (multipart/form-data):**
```
file: <binary file data>
purpose: "assistants" | "retrieval"
```

**Response (201):**
```json
{
  "file_id": "file_new789",
  "filename": "document.pdf",
  "size": 1024567,
  "purpose": "retrieval",
  "uploaded_at": "2024-01-15T13:15:00Z"
}
```

### DELETE /files/{file_id}

Delete a file.

**Response (204):**
No content (successful deletion)

---

## Credits & Billing

### GET /credits/balance

Get current thread usage and limits.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "thread_counter": 45,
  "thread_max": 100,
  "threads_remaining": 55,
  "subscription_tier": "standard"
}
```

### POST /credits/checkout

Create a Stripe checkout session for purchasing threads.

**Request:**
```json
{
  "quantity": 1000,
  "amount": 80.00
}
```

**Response (200):**
```json
{
  "url": "https://checkout.stripe.com/session_...",
  "session_id": "cs_..."
}
```

**Pricing:**
- < 500 threads: €0.10/thread
- 500-999 threads: €0.09/thread
- 1000+ threads: €0.08/thread

---

## Virtual Database

Threads can serve as structured, persistent storage.

### GET /db/{project_id}/{thread_id}

Get all structured data from a thread.

**Headers:**
```
Authorization: Bearer <project_access_token>
```

**Response (200):**
```json
{
  "user_preferences": {
    "theme": "dark",
    "language": "en"
  },
  "status": "active",
  "last_action": "checkout"
}
```

### GET /db/{project_id}/{thread_id}/{key}

Get specific key from thread state.

**Response (200):**
```json
{
  "theme": "dark",
  "language": "en"
}
```

### PUT /db/{project_id}/{thread_id}/{key}

Set a key-value pair in thread state.

**Request:**
```json
{
  "value": {
    "theme": "light",
    "language": "es"
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "key": "user_preferences",
  "value": {
    "theme": "light",
    "language": "es"
  }
}
```

---

## Best Practices

### 1. Token Management
- Cache tokens and refresh on 401 errors
- Store tokens securely (never in version control)
- Use project-specific tokens for multi-tenant apps

### 2. Error Handling
- Always implement retry logic for 429 and 500+ errors
- Use exponential backoff with jitter
- Log errors for debugging

### 3. Rate Limiting
- Implement client-side throttling
- Respect `X-RateLimit-*` headers
- Consider upgrading tier for higher limits

### 4. Security
- Use HTTPS for all requests
- Validate SSL certificates in production
- Never expose API keys in frontend code
- Use environment variables for credentials

### 5. Performance
- Use streaming for long-running conversations
- Implement pagination for large result sets
- Cache frequently accessed data
- Batch operations when possible

---

## Code Examples

See [README.md](../README.md) for comprehensive Python SDK examples.

---

## Support

- **GitHub Issues:** https://github.com/thierryteisseire/epsimo-agent/issues
- **Documentation:** [SKILL.md](../SKILL.md)
- **Virtual DB Guide:** [docs/virtual_db_guide.md](../docs/virtual_db_guide.md)

---

**API Version:** 1.0  
**Last Updated:** 2024-02-11
