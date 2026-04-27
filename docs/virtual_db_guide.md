# Virtual Database Guide

The Virtual Database is Epsimo's built-in persistent storage layer. Instead of managing a separate database, your assistants store structured data directly in thread state — queryable from the CLI, SDK, and frontend.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Defining the Storage Tool](#1-defining-the-storage-tool)
- [Agent Writing to the Database](#2-agent-writing-to-the-database)
- [Reading Data via CLI](#3-reading-data-via-cli)
- [Reading Data via Python SDK](#4-reading-data-via-python-sdk)
- [Reading Data from the Frontend](#5-reading-data-from-the-frontend)
- [Seeding Data for Testing](#6-seeding-data-for-testing)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)

---

## How It Works

```
┌──────────────┐     update_database()     ┌──────────────────┐
│  Assistant    │ ──────────────────────►   │  Thread State     │
│  (GPT-4o)    │                           │  (Virtual DB)     │
└──────────────┘                           └──────┬───────────┘
                                                  │
                              ┌────────────────────┼────────────────────┐
                              │                    │                    │
                         ┌────▼────┐         ┌─────▼─────┐       ┌─────▼─────┐
                         │  CLI    │         │ Python SDK│       │ Frontend  │
                         │ epsimo  │         │ EpsimoClient     │ REST API  │
                         │ db query│         │ .db.get() │       │ /db/...   │
                         └─────────┘         └───────────┘       └───────────┘
```

1. **Agent writes** structured data using the `update_database` tool during conversation
2. **Data persists** in thread state, naturally partitioned per thread
3. **Query from anywhere** — CLI, SDK, or frontend REST calls

---

## 1. Defining the Storage Tool

Add the `update_database` tool to your assistant in `epsimo.yaml`:

```yaml
assistants:
  - name: "Support Agent"
    model: "gpt-4o"
    instructions: |
      You are a helpful support agent. Save user preferences
      and session data using the update_database tool.
    tools:
      - type: function
        name: update_database
        description: "Persist structured data to the thread state."
        parameters:
          type: object
          properties:
            key:
              type: string
              description: "The field name (e.g. 'user_preferences', 'order_status')"
            value:
              type: object
              description: "The JSON data to store"
          required: ["key", "value"]
```

Or use the pre-built `database_sync` tool from the tool library:

```yaml
assistants:
  - name: "Support Agent"
    model: "gpt-4o"
    instructions: "You are a helpful support agent."
    tools:
      - type: function
        name: update_database
        description: "Persist structured JSON data to the conversation state for long-term memory."
        parameters:
          type: object
          properties:
            key: { type: string, description: "The data category" }
            value: { type: object, description: "The JSON data to store" }
          required: ["key", "value"]
```

---

## 2. Agent Writing to the Database

When the assistant decides to save data, it calls the tool automatically:

```json
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

The data is stored in the thread's state and persists across messages. The assistant can read it back in future turns because it's part of the thread context.

---

## 3. Reading Data via CLI

### Query all data in a thread

```bash
epsimo db query --project-id proj_abc --thread-id thread_123
```

Output:
```json
{
  "user_preferences": {
    "theme": "dark",
    "language": "en",
    "notifications": true
  },
  "order_status": "shipped"
}
```

### Get a specific key

```bash
epsimo db get --project-id proj_abc --thread-id thread_123 --key user_preferences
```

### Using the TUI

Launch `epsimo tui`, navigate to the **DB** tab (press `5`), and browse thread state interactively. Or use the `/db` slash command inside a chat session.

---

## 4. Reading Data via Python SDK

```python
from epsimo import EpsimoClient

client = EpsimoClient()

# Get all structured data from a thread
db_state = client.db.get_all("proj_abc", "thread_123")
print(db_state)
# {"user_preferences": {"theme": "dark", ...}, "order_status": "shipped"}

# Get a specific key
prefs = client.db.get("proj_abc", "thread_123", "user_preferences")
print(f"Theme: {prefs.get('theme')}")  # "dark"

# Set a value (for seeding or testing)
client.db.set("proj_abc", "thread_123", "status", "active")
```

---

## 5. Reading Data from the Frontend

Use the REST API directly from your frontend application:

```typescript
// Fetch all thread state
const response = await fetch(
  `https://backend.epsimoagents.com/db/${projectId}/${threadId}`,
  { headers: { Authorization: `Bearer ${projectToken}` } }
);
const dbState = await response.json();

// Use in your UI
if (dbState.user_preferences?.theme === "dark") {
  applyDarkTheme();
}
```

### With the React UI Kit

```tsx
import { useEffect, useState } from "react";

function UserPreferences({ projectId, threadId, token }) {
  const [prefs, setPrefs] = useState(null);

  useEffect(() => {
    fetch(`https://backend.epsimoagents.com/db/${projectId}/${threadId}/user_preferences`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(setPrefs);
  }, [projectId, threadId, token]);

  if (!prefs) return <p>Loading...</p>;

  return (
    <div>
      <p>Theme: {prefs.theme}</p>
      <p>Language: {prefs.language}</p>
    </div>
  );
}
```

---

## 6. Seeding Data for Testing

Use the CLI or SDK to pre-populate thread state before testing:

```bash
# Seed user preferences
epsimo db set --project-id proj_abc --thread-id thread_123 \
  --key "user_preferences" --value '{"theme":"dark","language":"en"}'

# Seed order status
epsimo db set --project-id proj_abc --thread-id thread_123 \
  --key "order_status" --value '"processing"'
```

```python
# SDK seeding
client.db.set("proj_abc", "thread_123", "user_preferences", {
    "theme": "dark",
    "language": "en"
})
client.db.set("proj_abc", "thread_123", "order_status", "processing")
```

---

## Common Patterns

### User Profile Storage

```yaml
# Assistant instruction snippet
instructions: |
  When the user shares personal preferences, save them using update_database
  with key "user_profile". Include name, preferences, and any relevant context.
```

### Session State Tracking

```python
# Track conversation milestones
client.db.set(project_id, thread_id, "session_state", {
    "step": "onboarding_complete",
    "started_at": "2024-01-15T10:00:00Z",
    "actions_taken": ["intro", "preferences_set", "first_query"]
})
```

### Multi-key Data Model

```
Thread State:
├── user_profile      → {name, email, preferences}
├── session_state     → {step, started_at, actions}
├── order_history     → [{id, status, date}, ...]
└── support_tickets   → [{id, subject, resolved}, ...]
```

---

## Best Practices

1. **Use descriptive key names** — `user_preferences` not `prefs`
2. **Keep values as JSON objects** — easier to extend later
3. **Partition by concern** — separate keys for profile, orders, settings
4. **Don't store secrets** — thread state is readable by anyone with project access
5. **Use seeding for tests** — pre-populate state via CLI before running test scenarios
6. **Monitor state size** — thread state is loaded with each message, so keep it reasonable

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/db/{project_id}/{thread_id}` | Get all thread state |
| GET | `/db/{project_id}/{thread_id}/{key}` | Get specific key |
| PUT | `/db/{project_id}/{thread_id}/{key}` | Set a key-value pair |

See [references/api_reference.md](../references/api_reference.md) for full API documentation.
