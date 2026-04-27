# Configuration Reference

The `epsimo.yaml` file is the central configuration for your Epsimo project. It defines your project identity, assistants, and their tools.

---

## File Location

The CLI looks for `epsimo.yaml` in the **current working directory**. Create it with:

```bash
epsimo init              # Auto-generates epsimo.yaml
```

Or create it manually.

---

## Full Schema

```yaml
# Required: Project ID (assigned by the platform)
project_id: "proj_abc123"

# Required: Human-readable project name
name: "My AI App"

# Required: List of assistant configurations
assistants:
  - name: "Assistant Name"          # Required: unique name within project
    model: "gpt-4o"                 # Optional: model to use (default: gpt-4o)
    instructions: |                 # Optional: system prompt
      You are a helpful assistant.
    tools:                          # Optional: list of tools
      - type: retrieval
      - type: search_tavily
      - type: function
        name: "tool_name"
        description: "What the tool does"
        parameters:
          type: object
          properties:
            key: { type: string }
          required: ["key"]
```

---

## Fields

### Top-level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | Yes | UUID assigned when you run `epsimo init` |
| `name` | string | Yes | Display name for the project |
| `assistants` | list | Yes | One or more assistant configurations |

### Assistant

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | — | Unique name within the project. Used to match during `epsimo deploy` |
| `model` | string | No | `gpt-4o` | LLM model identifier |
| `instructions` | string | No | `""` | System prompt / instructions for the assistant |
| `tools` | list | No | `[]` | Tools available to the assistant |

### Tool Types

#### Built-in tools

These require only a `type` field:

| Type | Description |
|------|-------------|
| `retrieval` | Search in uploaded files (RAG) |
| `search_tavily` | Web search via Tavily with source attribution |
| `ddg_search` | Web search via DuckDuckGo |

```yaml
tools:
  - type: retrieval
  - type: search_tavily
```

#### Function tools

Custom tools the assistant can call. Require `name`, `description`, and `parameters`:

```yaml
tools:
  - type: function
    name: update_database
    description: "Persist structured data to thread state."
    parameters:
      type: object
      properties:
        key:
          type: string
          description: "The data category"
        value:
          type: object
          description: "The JSON data to store"
      required: ["key", "value"]
```

---

## Examples

### Minimal configuration

```yaml
project_id: proj_abc123
name: Simple Bot
assistants:
  - name: default-assistant
    model: gpt-4o
    instructions: You are a helpful assistant.
```

### Multi-assistant project

```yaml
project_id: proj_abc123
name: Customer Support Hub
assistants:
  - name: "Support Agent"
    model: "gpt-4o"
    instructions: |
      You are a customer support agent. Help users with their questions.
      Save important user information using the update_database tool.
    tools:
      - type: retrieval
      - type: function
        name: update_database
        description: "Save user data to thread state"
        parameters:
          type: object
          properties:
            key: { type: string }
            value: { type: object }
          required: ["key", "value"]

  - name: "Research Assistant"
    model: "gpt-4o"
    instructions: |
      You help with research tasks. Search the web for information
      and save findings to the database.
    tools:
      - type: search_tavily
      - type: function
        name: update_database
        description: "Save research findings"
        parameters:
          type: object
          properties:
            key: { type: string }
            value: { type: object }
          required: ["key", "value"]
```

### Assistant with multiple search tools

```yaml
project_id: proj_abc123
name: Research Hub
assistants:
  - name: "Deep Researcher"
    model: "gpt-4o"
    instructions: |
      You are a research assistant. Use Tavily for detailed searches
      and DuckDuckGo for quick lookups.
    tools:
      - type: search_tavily
      - type: ddg_search
      - type: retrieval
```

---

## Deployment

After editing `epsimo.yaml`, push changes to the platform:

```bash
epsimo deploy
```

The deploy command:
1. Reads `epsimo.yaml` from the current directory
2. Fetches existing assistants from the platform
3. **Creates** new assistants that don't exist yet (matched by `name`)
4. **Updates** existing assistants that match by `name`

Assistants that exist on the platform but are not in `epsimo.yaml` are **not deleted** — deploy is additive.

---

## Available Models

The `model` field accepts any model supported by the Epsimo platform. Common options:

| Model | Description |
|-------|-------------|
| `gpt-4o` | GPT-4o (recommended default) |
| `gpt-4o-mini` | Smaller, faster, cheaper GPT-4o variant |

---

## Environment Variables

These override or supplement `epsimo.yaml`:

| Variable | Description |
|----------|-------------|
| `EPSIMO_API_URL` | Override the API base URL (default: `https://backend.epsimoagents.com`) |
| `EPSIMO_API_KEY` | JWT token for SDK authentication |
| `EPSIMO_EMAIL` | Email for automatic authentication |
| `EPSIMO_PASSWORD` | Password for automatic authentication |

---

## Tool Library

Pre-built tool schemas are available in `epsimo/tools/library.yaml`. See the [README](../README.md#-tool-library) for the full list.
