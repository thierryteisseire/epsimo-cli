# Virtual Database via Epsimo Threads

This guide explains how to use Epsimo threads as a persistent, structured storage layer for your application using the **Virtual Database** pattern.

## The Concept

Instead of managing a separate database, your assistant can maintain its own structured state directly within an Epsimo thread. This data is persistent, indexed by thread, and can be queried both by the assistant and your frontend.

## 1. Defining the Storage Tool (Skill)

To allow an assistant to write to its database, provide it with a tool that handles data recording.

### Tool Definition (JSON)
```json
{
  "name": "update_database",
  "description": "Persist structured data to the thread state.",
  "parameters": {
    "type": "object",
    "properties": {
      "key": { "type": "string", "description": "The field name (e.g., 'user_preferences')" },
      "value": { "type": "object", "description": "The data to store (JSON object)" }
    },
    "required": ["key", "value"]
  }
}
```

## 2. Reading Data via SDK

Use the newly implemented `c.db` resource in the `epsimo` Python SDK to retrieve the structured state.

```python
from epsimo import EpsimoClient

client = EpsimoClient(api_key="your-token")

# Get everything
db = client.db.get_all(project_id, thread_id)

# Get specific key
preferences = client.db.get(project_id, thread_id, "user_preferences")
print(f"Theme: {preferences.get('theme')}")
```

## 3. Writing Data via CLI (Admin/Testing)

You can also manually seed coordinates into the "database" using the CLI:

```bash
epsimo db set --project-id PROJ_ID --thread-id THREAD_ID --key "status" --value '"active"'
```

## Benefits
- **Zero Configuration**: No database server required.
- **Contextual Storage**: Data is naturally partitioned by conversation.
- **Agent Awareness**: The assistant always "knows" what's in its DB because it is part of the thread state.
