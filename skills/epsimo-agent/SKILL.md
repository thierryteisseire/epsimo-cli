---
name: epsimo-agent
description: Comprehensive Epsimo AI platform SDK and CLI for managing agents, projects, threads, Virtual Database, and frontend design. Build AI apps with persistent state, streaming conversations, and React UI kit.
---

# Epsimo Agent Framework

> [!NOTE]
> This is a **Beta Release** (v0.2.0). Features and APIs may evolve based on feedback.

The Epsimo Agent Framework allows you to build sophisticated AI-powered applications with agents, persistent threads, and a "Virtual Database" state layer. It provides a unified **CLI**, a **Python SDK**, and a **React UI Kit**.

**Base URL:** `https://api.epsimoagents.com`  
**Frontend URL:** `https://app.epsimoagents.com`

---

## 🚀 Quick Start: Create an MVP in 3 Commands

The fastest way to build an Epsimo app is using the project generator:

```bash
# 1. Authenticate
epsimo auth login

# 2. Create a new Next.js project
epsimo create "My AI App"

# 3. Initialize and Deploy
cd my-ai-app
epsimo init
epsimo deploy
```

Your AI app is now live with persistent conversations, Virtual Database state, and a pre-built chat UI.

---

## 📦 Installation

### CLI & Python SDK

```bash
# Install dependencies
pip install -r requirements.txt

# Make CLI executable (if using from source)
chmod +x epsimo/cli.py
export PATH="$PATH:$(pwd)/epsimo"

# Or via npm (for Claude Code skills)
npm install -g epsimo-agent
```

**Dependencies:**
- `requests>=2.28.0`
- `pyyaml>=6.0`
- `click>=8.0.0`
- `python-dotenv>=0.19.0`

---

## 🔐 Authentication

### Login Flow

```bash
# Interactive login
epsimo auth login

# Login with environment variables
export EPSIMO_EMAIL=your@email.com
export EPSIMO_PASSWORD=your-password
epsimo auth login
```

### Programmatic Authentication

```python
from epsimo.auth import perform_login, get_token

# Login and get token
token = perform_login("your@email.com", "password")

# Get cached token (auto-refreshes if expired)
token = get_token()
```

### Token Management

Tokens are stored in `~/code/epsimo-frontend/.epsimo_token` and expire after **1 hour**.

**Token Storage Format:**
```json
{
  "access_token": "eyJhbG...",
  "token": "eyJhbG...",
  "jwt_token": "eyJhbG...",
  "expires_in": 3600
}
```

**Best Practices:**
- ✅ Use environment variables (`EPSIMO_API_KEY`) for production
- ✅ Never commit `.epsimo_token` to version control
- ✅ Implement token refresh on 401 errors
- ✅ Use project-specific tokens for multi-tenant apps

---

## 🛠️ Unified CLI (`epsimo`)

The `epsimo` CLI is the main tool for managing your agents and data.

### Authentication Commands

| Command | Description |
|---------|-------------|
| `epsimo auth login` | Interactive login with email/password |
| `epsimo whoami` | Display current user info and thread usage |

**Example:**
```bash
$ epsimo whoami
👤 Fetching user info...
Logged in as: user@example.com
Threads Used: 45/100
```

### Project Management

| Command | Description |
|---------|-------------|
| `epsimo projects` | List all projects |
| `epsimo projects --json` | List projects in JSON format |
| `epsimo create <name>` | Scaffold a full Next.js application with Epsimo |
| `epsimo init` | Link a local directory to an Epsimo project |
| `epsimo deploy` | Sync your `epsimo.yaml` configuration to the platform |

**Example:**
```bash
$ epsimo projects
📁 Fetching projects...
ID                                      | Name
-----------------------------------------------------------------
proj_abc123                             | Customer Support Bot
proj_xyz789                             | Research Assistant
```

### Virtual Database Commands

Threads can serve as a persistent structured storage layer.

| Command | Description |
|---------|-------------|
| `epsimo db query --project-id <P_ID> --thread-id <T_ID>` | View all structured thread state |
| `epsimo db get --project-id <P_ID> --thread-id <T_ID> --key <K>` | Get specific key from thread state |
| `epsimo db set --project-id <P_ID> --thread-id <T_ID> --key <K> --value <V>` | Seed state for testing |

**Example:**
```bash
$ epsimo db query --project-id proj_abc --thread-id thread_123
{
  "user_preferences": {
    "theme": "dark",
    "language": "en"
  },
  "status": "active"
}

$ epsimo db set --project-id proj_abc --thread-id thread_123 \
  --key "status" --value '"completed"'
```

### Credits & Billing

| Command | Description |
|---------|-------------|
| `epsimo credits balance` | Check current thread balance and subscription tier |
| `epsimo credits buy --quantity <N>` | Generate a Stripe checkout URL for purchasing threads |

**Example:**
```bash
$ epsimo credits balance
💳 Checking balance...

=== Thread Balance ===
Threads Used:      45
Total Allowance:   100
Threads Remaining: 55
======================

$ epsimo credits buy --quantity 1000
🛒 Preparing purchase of 1000 threads...
ℹ️  Estimated cost: 80.0 EUR

✅ Checkout session created successfully!
Please visit this URL to complete your purchase:

https://checkout.stripe.com/session_...
```

**Pricing:**
- < 500 threads: €0.10/thread
- 500-999 threads: €0.09/thread
- 1000+ threads: €0.08/thread

### Resource Listing

| Command | Description |
|---------|-------------|
| `epsimo assistants --project-id <P_ID>` | List all assistants in a project |
| `epsimo assistants --project-id <P_ID> --json` | List assistants in JSON format |
| `epsimo threads --project-id <P_ID>` | List all threads in a project |

---

## 📚 Python SDK

### Installation & Setup

```python
from epsimo import EpsimoClient

# Initialize with API key (JWT token)
client = EpsimoClient(api_key="your-token-here")

# Or use environment variable
# export EPSIMO_API_KEY=your-token-here
client = EpsimoClient()

# Or use custom base URL
client = EpsimoClient(
    api_key="token",
    base_url="https://api.epsimoagents.com"
)
```

### Resource Clients

The SDK provides dedicated resource clients for each entity type:

| Resource | Access via | Purpose |
|----------|-----------|---------|
| **Projects** | `client.projects` | Top-level containers |
| **Assistants** | `client.assistants` | AI agents with instructions |
| **Threads** | `client.threads` | Persistent conversations |
| **Files** | `client.files` | Document uploads |
| **Credits** | `client.credits` | Billing & usage |
| **Database** | `client.db` | Virtual DB access |

### Projects

```python
# List all projects
projects = client.projects.list()
for p in projects:
    print(f"{p['project_id']}: {p['name']}")

# Create a new project
project = client.projects.create(
    name="My AI Project",
    description="Customer support automation"
)
print(f"Created project: {project['project_id']}")

# Get project details (includes project-specific token)
details = client.projects.get(project_id="proj_abc123")
project_token = details['access_token']

# Delete a project
client.projects.delete(project_id="proj_abc123")
```

### Assistants

```python
# List assistants in a project
assistants = client.assistants.list(project_id="proj_abc123")

# Create an assistant
assistant = client.assistants.create(
    project_id="proj_abc123",
    config={
        "name": "Support Agent",
        "instructions": "You are a helpful customer support agent.",
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
                "description": "Save structured data to thread state",
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
    }
)

# Get assistant details
assistant = client.assistants.get(
    project_id="proj_abc123",
    assistant_id="asst_xyz789"
)

# Delete an assistant
client.assistants.delete(
    project_id="proj_abc123",
    assistant_id="asst_xyz789"
)
```

### Threads

```python
# List threads in a project
threads = client.threads.list(project_id="proj_abc123")

# Create a new thread
thread = client.threads.create(
    project_id="proj_abc123",
    assistant_id="asst_xyz789",
    name="Customer #1234",
    metadata={
        "configurable": {},
        "type": "thread"
    }
)

# Get thread details and messages
thread_data = client.threads.get(
    project_id="proj_abc123",
    thread_id="thread_123"
)
print(f"Messages: {len(thread_data['messages'])}")

# Delete a thread
client.threads.delete(
    project_id="proj_abc123",
    thread_id="thread_123"
)
```

### Streaming Conversations

```python
# Stream assistant responses
for chunk in client.threads.run_stream(
    project_id="proj_abc123",
    thread_id="thread_123",
    assistant_id="asst_xyz789",
    message="Hello, how can you help me?"
):
    print(chunk, end="", flush=True)
```

### Files

```python
# List files in a project
files = client.files.list(project_id="proj_abc123")

# Upload a file
file = client.files.upload(
    project_id="proj_abc123",
    file_path="/path/to/document.pdf",
    purpose="retrieval"  # or "assistants"
)

# Delete a file
client.files.delete(
    project_id="proj_abc123",
    file_id="file_abc123"
)
```

### Credits

```python
# Get current balance
balance = client.credits.get_balance()
print(f"Threads used: {balance['thread_counter']}/{balance['thread_max']}")

# Create checkout session
checkout = client.credits.create_checkout_session(
    quantity=1000,
    amount=80.00
)
print(f"Checkout URL: {checkout['url']}")
```

### Virtual Database

```python
# Get all structured data from a thread
db_state = client.db.get_all(
    project_id="proj_abc123",
    thread_id="thread_123"
)
print(f"User preferences: {db_state.get('user_preferences')}")

# Get specific key
user_prefs = client.db.get(
    project_id="proj_abc123",
    thread_id="thread_123",
    key="user_preferences"
)
print(f"Theme: {user_prefs.get('theme')}")

# Set value (for seeding/testing)
client.db.set(
    project_id="proj_abc123",
    thread_id="thread_123",
    key="status",
    value="active"
)
```

---

## 🎨 React UI Kit

The UI Kit provides high-level components for immediate integration.

### ThreadChat Component

A modern, dark-themed chat interface with streaming and tool support.

```tsx
import { ThreadChat } from "@/components/epsimo";

export default function App() {
  return (
    <ThreadChat 
      assistantId="asst_xyz789"
      projectId="proj_abc123"
      placeholder="Ask me anything..."
      theme="dark"
    />
  );
}
```

**Features:**
- ✅ Real-time streaming responses
- ✅ Tool call visualization
- ✅ Message history
- ✅ Dark/light theme support
- ✅ Mobile responsive

### useChat Hook (Headless)

For custom UI implementations:

```tsx
import { useChat } from "@/hooks/epsimo";

export default function CustomChat() {
  const { 
    messages, 
    sendMessage, 
    isLoading,
    error
  } = useChat({
    projectId: "proj_abc123",
    threadId: "thread_123",
    assistantId: "asst_xyz789"
  });

  return (
    <div>
      {messages.map(msg => (
        <div key={msg.id} className={msg.role}>
          {msg.content}
        </div>
      ))}
      
      <button 
        onClick={() => sendMessage("Hello")} 
        disabled={isLoading}
      >
        {isLoading ? "Sending..." : "Send"}
      </button>
      
      {error && <div className="error">{error}</div>}
    </div>
  );
}
```

---

## 📦 Tool Library

Found in `epsimo/tools/library.yaml`, this collection provides reusable JSON schemas for common tasks.

### Available Tools

| Tool | Type | Description | Configuration |
|------|------|-------------|---------------|
| **database_sync** | function | Allow agents to write structured JSON to thread state | `key`, `value` parameters |
| **web_search_tavily** | search_tavily | Advanced search with source attribution | `max_results: 5` |
| **web_search_ddg** | ddg_search | Fast DuckDuckGo search for simple queries | None |
| **retrieval_optimized** | retrieval | High-accuracy document search in uploaded files | `top_k: 5`, `score_threshold: 0.7` |
| **task_management** | function | Track and update user tasks | `action`, `details` parameters |

### Using Tools in epsimo.yaml

```yaml
assistants:
  - name: "Research Assistant"
    model: "gpt-4o"
    instructions: "You help with research tasks and save findings to the database."
    tools:
      - type: search_tavily
        max_results: 5
      - type: function
        name: update_database
        description: "Persist research findings to thread state"
        parameters:
          type: object
          properties:
            key: 
              type: string
              description: "The data category (e.g. 'research_notes')"
            value: 
              type: object
              description: "The JSON data to store"
          required: ["key", "value"]
```

---

## 💾 Virtual Database Pattern

Threads serve as persistent, structured storage — eliminating the need for a separate database.

### How It Works

1. **Agent writes to DB** using the `update_database` tool
2. **Data persists** in thread state (indexed by thread)
3. **Query from SDK, CLI, or frontend**

### Benefits

- ✅ **Zero Configuration** — No database server required
- ✅ **Contextual Storage** — Data is naturally partitioned by conversation
- ✅ **Agent Awareness** — The assistant always "knows" what's in its DB
- ✅ **Queryable** — Access from both agent code and application code

### Example Workflow

**Step 1:** Assistant saves user preferences

```json
// Agent calls update_database tool
{
  "name": "update_database",
  "arguments": {
    "key": "user_preferences",
    "value": {
      "theme": "dark",
      "language": "en",
      "notifications": true
    }
  }
}
```

**Step 2:** Query from your application

```python
# Python SDK
prefs = client.db.get(project_id, thread_id, "user_preferences")
if prefs.get('theme') == 'dark':
    apply_dark_theme()
```

**Step 3:** CLI inspection

```bash
$ epsimo db query --project-id proj_123 --thread-id thread_456
{
  "user_preferences": {
    "theme": "dark",
    "language": "en",
    "notifications": true
  }
}
```

See [docs/virtual_db_guide.md](docs/virtual_db_guide.md) for comprehensive guide.

---

## 🔧 Error Handling & Best Practices

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue processing |
| 201 | Created | Capture returned ID |
| 401 | Unauthorized | Refresh token or re-authenticate |
| 403 | Forbidden | Check user/project permissions |
| 404 | Not Found | Verify resource ID |
| 429 | Rate Limited | Implement exponential backoff |
| 500 | Server Error | Retry with exponential backoff |

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
                print(f"⏳ Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            elif e.response.status_code >= 500:
                # Server error - retry with backoff
                wait_time = min(10 * (2 ** attempt), 60)  # Max 1 minute
                print(f"⚠️ Server error. Waiting {wait_time}s...")
                time.sleep(wait_time)
            elif e.response.status_code == 401:
                # Token expired - try to refresh
                print("🔑 Token expired. Re-authenticating...")
                raise
            else:
                # Other errors - don't retry
                raise

    raise Exception(f"Max retries ({max_retries}) exceeded")
```

### Rate Limits

| Tier | Limit |
|------|-------|
| Free | 60 requests/minute |
| Standard | 300 requests/minute |
| Premium | 1,000 requests/minute |

### Security Best Practices

1. **API Key Management**
   - Never commit `.epsimo_token` to version control
   - Use environment variables (`EPSIMO_API_KEY`)
   - Rotate tokens regularly
   - Use different tokens for dev/staging/production

2. **Data Privacy**
   - Always use project-scoped tokens for multi-tenant apps
   - Implement proper access controls at application layer
   - Audit stored thread data regularly
   - Tag sensitive information appropriately

3. **Network Security**
   - Always use HTTPS endpoints
   - Validate SSL certificates in production
   - Consider using API gateways for additional security layers
   - Monitor API usage for unusual patterns

---

## 🧪 Verification & Testing

Ensure your environment is correctly configured:

```bash
# Verify skill configuration
python3 verify_skill.py

# Run comprehensive E2E test suite
python3 scripts/test_all_skills.py

# Test streaming functionality
python3 scripts/test_streaming.py

# Test Virtual DB operations
python3 scripts/test_vdb.py
```

**Verification Steps:**
1. ✅ Authentication successful
2. ✅ Project creation
3. ✅ Assistant creation
4. ✅ Thread creation
5. ✅ Resource listing
6. ✅ Cleanup (automatic deletion)

---

## 🔍 Troubleshooting

### Authentication Issues

**Problem:** `❌ Not logged in. Use 'epsimo auth'.`

**Solution:**
```bash
epsimo auth login
# Or set environment variables
export EPSIMO_EMAIL=your@email.com
export EPSIMO_PASSWORD=your-password
```

### Token Expiration

**Problem:** `401 Unauthorized - Token has expired`

**Solution:**
```python
from epsimo.auth import perform_login

# Re-authenticate
token = perform_login(email, password)
```

### Rate Limiting

**Problem:** `429 Too Many Requests`

**Solution:**
- Implement exponential backoff (see examples above)
- Upgrade to higher tier
- Implement client-side request throttling

### Project-Scoped Operations Failing

**Problem:** `403 Forbidden` when accessing assistants/threads

**Solution:**
```python
# Get project-specific token
project = client.projects.get(project_id)
project_token = project['access_token']

# Use project token for scoped operations
project_client = EpsimoClient(api_key=project_token)
assistants = project_client.assistants.list(project_id)
```

---

## 📖 Reference Documentation

- **Full API Reference**: [references/api_reference.md](references/api_reference.md)
- **Virtual DB Guide**: [docs/virtual_db_guide.md](docs/virtual_db_guide.md)
- **README**: [README.md](README.md)
- **Tool Library**: [epsimo/tools/library.yaml](epsimo/tools/library.yaml)

---

## 🔗 Links

- **GitHub Repository**: https://github.com/thierryteisseire/epsimo-agent
- **Web Application**: https://app.epsimoagents.com
- **API Base URL**: https://api.epsimoagents.com

---

## 📋 System Architecture

```
Epsimo Platform
├── Authentication Layer (JWT tokens)
├── Projects (top-level containers)
│   ├── Assistants (AI agents with instructions)
│   ├── Threads (persistent conversations)
│   │   └── Virtual Database (structured state)
│   └── Files (uploaded documents)
└── Billing (thread-based credits)

Client Tools
├── CLI (epsimo command)
├── Python SDK (EpsimoClient)
└── React UI Kit (ThreadChat, useChat)
```

---

**Version:** 0.2.0  
**License:** MIT  
**Author:** Thierry Teisseire

For questions or issues, visit [GitHub Issues](https://github.com/thierryteisseire/epsimo-agent/issues).
