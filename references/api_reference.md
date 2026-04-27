# Epsimo API Reference

Complete reference for the Epsimo Agent Platform REST API.

**Base URL:** `https://backend.epsimoagents.com`

---

## Table of Contents

1. [Authentication](#authentication)
2. [HTTP Status Codes](#http-status-codes)
3. [Error Handling](#error-handling)
4. [Rate Limits](#rate-limits)
5. [Projects](#projects)
6. [Assistants](#assistants)
7. [Threads](#threads)
8. [Runs (Streaming)](#runs-streaming)
9. [Files](#files)
10. [Credits & Billing](#credits--billing)
11. [Virtual Database](#virtual-database)
12. [Tools](#tools)

---

## Authentication

All API requests require a JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens expire after **1 hour**. Re-authenticate to get a new token.

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

Authenticate and receive an access token.

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

### GET /auth/thread-info

Get current user info and thread usage. Also used as the balance endpoint.

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

### GET /auth/user-info

Get user profile information.

**Response (200):**
```json
{
  "email": "user@example.com",
  "user_id": "usr_123"
}
```

---

## HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue processing |
| 201 | Created | Capture returned ID |
| 204 | No Content | Deletion succeeded |
| 400 | Bad Request | Validate request payload |
| 401 | Unauthorized | Refresh token or re-authenticate |
| 403 | Forbidden | Check user/project permissions |
| 404 | Not Found | Verify resource ID |
| 409 | Conflict | Check for duplicate resources |
| 422 | Validation Error | Review error details |
| 429 | Too Many Requests | Implement exponential backoff |
| 500 | Server Error | Retry with backoff |
| 503 | Service Unavailable | Wait and retry |

---

## Error Handling

### Standard Error Format

```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

### Retry with Exponential Backoff

```python
import time
import requests

def request_with_retry(method, url, headers, json_data=None, max_retries=5):
    for attempt in range(max_retries):
        resp = requests.request(method, url, headers=headers, json=json_data)
        if resp.ok:
            return resp.json() if resp.content else None
        if resp.status_code == 429:
            time.sleep(min(60 * (2 ** attempt), 300))
        elif resp.status_code >= 500:
            time.sleep(min(10 * (2 ** attempt), 60))
        elif resp.status_code == 401:
            raise Exception("Token expired — re-authenticate")
        else:
            resp.raise_for_status()
    raise Exception(f"Max retries ({max_retries}) exceeded")
```

---

## Rate Limits

| Tier | Limit |
|------|-------|
| Free | 60 requests/minute |
| Standard | 300 requests/minute |
| Premium | 1,000 requests/minute |

Rate limit headers:
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 245
X-RateLimit-Reset: 1672531200
```

---

## Projects

Projects are top-level containers for assistants, threads, and files. Use your **user-level token** for project operations.

### GET /projects/

List all projects.

**Response (200):**
```json
[
  {
    "project_id": "proj_abc123",
    "name": "My AI Project",
    "description": "Customer support automation",
    "access_token": "proj_token_...",
    "created_at": "2024-01-15T10:30:00Z"
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
  "metadata": {}
}
```

**Response (201):**
```json
{
  "project_id": "proj_xyz789",
  "name": "My New Project",
  "access_token": "proj_token_...",
  "created_at": "2024-01-15T11:00:00Z"
}
```

### GET /projects/{project_id}

Get project details. The response includes a **project-specific access token** — use this token for all assistant, thread, and file operations within the project.

**Response (200):**
```json
{
  "project_id": "proj_abc123",
  "name": "My AI Project",
  "access_token": "proj_token_...",
  "token": "proj_token_...",
  "jwt_token": "proj_token_..."
}
```

### PUT /projects/{project_id}

Update a project.

**Request:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "metadata": {}
}
```

### DELETE /projects/{project_id}?confirm=true

Delete a project and all associated resources. Requires `confirm=true` query parameter.

**Response (204):** No content

---

## Assistants

Assistants are AI agents with instructions and tool configurations. All assistant endpoints require a **project-scoped token** (from `GET /projects/{project_id}`).

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
      "configurable": {
        "type": "agent",
        "type==agent/agent_type": "agent",
        "type==agent/system_message": "You are a helpful agent.",
        "type==agent/tools": [...]
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
    "configurable": {
      "type": "agent",
      "type==agent/agent_type": "agent",
      "type==agent/system_message": "You help with research tasks.",
      "type==agent/tools": [
        {
          "id": "search_tavily-abc123",
          "name": "Search (Tavily)",
          "type": "search_tavily",
          "description": "Uses the Tavily search engine.",
          "config": {}
        }
      ]
    }
  },
  "metadata": {},
  "tags": [],
  "public": false
}
```

**Response (201):**
```json
{
  "assistant_id": "asst_xyz789",
  "name": "Research Assistant",
  "config": { ... }
}
```

### GET /assistants/{assistant_id}

Get assistant details.

### PUT /assistants/{assistant_id}

Update an assistant's configuration.

### DELETE /assistants/{assistant_id}

Delete an assistant. **Response (204):** No content

---

## Threads

Threads represent persistent conversation contexts. All thread endpoints require a **project-scoped token**.

### GET /threads/

List all threads in a project.

**Response (200):**
```json
{
  "threads": [
    {
      "thread_id": "thread_abc123",
      "name": "Customer #1234",
      "assistant_id": "asst_xyz789",
      "metadata": { "type": "thread" },
      "created_at": "2024-01-15T12:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /threads/

Create a new thread.

**Request:**
```json
{
  "name": "Customer Support Session",
  "assistant_id": "asst_xyz789",
  "metadata": { "type": "thread" }
}
```

**Response (201):**
```json
{
  "thread_id": "thread_new123",
  "name": "Customer Support Session",
  "assistant_id": "asst_xyz789"
}
```

### GET /threads/{thread_id}

Get thread details.

### GET /threads/{thread_id}/state

Get the thread's structured state (Virtual Database).

**Response (200):**
```json
{
  "values": {
    "user_preferences": { "theme": "dark" },
    "status": "active"
  }
}
```

### POST /threads/{thread_id}/state

Update the thread's structured state.

**Request:**
```json
{
  "values": {
    "status": "completed"
  },
  "config": {}
}
```

### GET /threads/{thread_id}/history

Get thread message history.

### PUT /threads/{thread_id}

Update thread metadata.

### DELETE /threads/{thread_id}

Delete a thread. **Response (204):** No content

---

## Runs (Streaming)

### POST /runs/stream

Send a message and stream the assistant's response via Server-Sent Events (SSE).

**Headers:**
```
Authorization: Bearer <project_access_token>
Accept: text/event-stream
```

**Request:**
```json
{
  "thread_id": "thread_123",
  "assistant_id": "asst_xyz",
  "input": [
    { "role": "user", "content": "What's the weather?", "type": "human" }
  ],
  "stream_mode": ["messages", "events", "values"]
}
```

**Response (SSE stream):**
```
event: messages
data: [{"type": "ai", "content": "Let me check", "tool_calls": [...]}]

event: messages
data: [{"type": "tool", "content": "Weather is sunny", "tool_call_id": "tc_123"}]

event: messages
data: [{"type": "ai", "content": "The weather is sunny today!"}]

data: [DONE]
```

**Stream event types:**
- `messages` — AI responses and tool call results
- `events` — Internal agent events
- `values` — Updated thread state values

---

## Files

File operations are scoped to assistants. Requires a **project-scoped token**.

### GET /assistants/{assistant_id}/files

List files attached to an assistant.

**Response (200):**
```json
[
  {
    "file_id": "file_abc123",
    "filename": "document.pdf",
    "size": 1024567,
    "uploaded_at": "2024-01-15T13:00:00Z"
  }
]
```

### POST /assistants/{assistant_id}/files

Upload a file (multipart/form-data).

**Request:**
```
Content-Type: multipart/form-data
files: <binary file data>
```

**Response (201):**
```json
{
  "file_id": "file_new789",
  "filename": "document.pdf",
  "size": 1024567
}
```

### DELETE /assistants/{assistant_id}/files/{file_id}

Delete a file. **Response (204):** No content

---

## Credits & Billing

### GET /auth/thread-info

Get current thread balance (same endpoint as user info).

**Response (200):**
```json
{
  "thread_counter": 45,
  "thread_max": 100,
  "email": "user@example.com"
}
```

### POST /checkout/create-checkout-session

Create a Stripe checkout session for purchasing threads.

**Request:**
```json
{
  "quantity": 1000
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
| Quantity | Price per Thread |
|----------|-----------------|
| < 500 | €0.10 |
| 500–999 | €0.09 |
| 1000+ | €0.08 |

---

## Virtual Database

The Virtual Database uses thread state as structured storage. These are convenience wrappers around the thread state endpoints.

### GET /threads/{thread_id}/state → `values`

Get all structured data. Extract the `values` field from the response.

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://backend.epsimoagents.com/threads/thread_123/state
```

### POST /threads/{thread_id}/state

Set key-value pairs in thread state.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"values": {"status": "active"}, "config": {}}' \
  https://backend.epsimoagents.com/threads/thread_123/state
```

See [docs/virtual_db_guide.md](../docs/virtual_db_guide.md) for patterns and examples.

---

## Tools

### GET /tools/

List available tool types.

### GET /tools/{tool_type}

Get details for a specific tool type.

### GET /tools/{tool_type}/health

Health-check a tool to verify it's working.

---

## Best Practices

1. **Use project-scoped tokens** — Get a project token via `GET /projects/{id}` and use it for all assistant/thread/file operations within that project.
2. **Implement retry logic** — Always handle 429 and 5xx errors with exponential backoff.
3. **Use streaming** — For conversations, use `/runs/stream` with SSE for real-time responses.
4. **Cache tokens** — Store tokens in `~/.epsimo_token` and refresh on 401 errors.
5. **Never expose tokens in frontend code** — Use a backend proxy for browser-based apps.

---

## SDK Mapping

| SDK Method | HTTP | Endpoint |
|------------|------|----------|
| `client.projects.list()` | GET | `/projects/` |
| `client.projects.create(name, desc)` | POST | `/projects/` |
| `client.projects.get(id)` | GET | `/projects/{id}` |
| `client.projects.delete(id)` | DELETE | `/projects/{id}?confirm=true` |
| `client.assistants.list(pid)` | GET | `/assistants/` |
| `client.assistants.create(pid, ...)` | POST | `/assistants/` |
| `client.assistants.get(pid, aid)` | GET | `/assistants/{aid}` |
| `client.assistants.delete(pid, aid)` | DELETE | `/assistants/{aid}` |
| `client.threads.list(pid)` | GET | `/threads/` |
| `client.threads.create(pid, ...)` | POST | `/threads/` |
| `client.threads.get(pid, tid)` | GET | `/threads/{tid}` |
| `client.threads.get_state(pid, tid)` | GET | `/threads/{tid}/state` |
| `client.threads.set_state(pid, tid, vals)` | POST | `/threads/{tid}/state` |
| `client.threads.delete(pid, tid)` | DELETE | `/threads/{tid}` |
| `client.threads.run_stream(...)` | POST | `/runs/stream` |
| `client.files.list(pid, aid)` | GET | `/assistants/{aid}/files` |
| `client.files.upload(pid, aid, path)` | POST | `/assistants/{aid}/files` |
| `client.files.delete(pid, aid, fid)` | DELETE | `/assistants/{aid}/files/{fid}` |
| `client.credits.get_balance()` | GET | `/auth/thread-info` |
| `client.credits.create_checkout_session(qty)` | POST | `/checkout/create-checkout-session` |

---

## Support

- **GitHub Issues:** [github.com/thierryteisseire/epsimo-cli/issues](https://github.com/thierryteisseire/epsimo-cli/issues)
- **Documentation:** [README.md](../README.md)
- **Virtual DB Guide:** [docs/virtual_db_guide.md](../docs/virtual_db_guide.md)

---

**API Version:** 1.0
**Last Updated:** 2026-04-27
