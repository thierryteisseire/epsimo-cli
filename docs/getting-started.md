# Getting Started with Epsimo

This guide walks you through installing the Epsimo CLI, creating your first project, and chatting with an AI assistant — all from the terminal.

---

## Prerequisites

- **Python 3.8+** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 14+** — [nodejs.org](https://nodejs.org/) (for npm install method)
- **Git** — for cloning the repo (source install only)

---

## Step 1: Install the CLI

Choose one method:

### Option A: npm (recommended)

```bash
npm install -g epsimo-cli
```

### Option B: One-line installer (macOS / Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/thierryteisseire/epsimo-cli/main/install.sh | bash
```

### Option C: From source

```bash
git clone https://github.com/thierryteisseire/epsimo-cli.git
cd epsimo-cli
pip install -e .
```

Verify the installation:

```bash
epsimo --version
# epsimo 0.3.3
```

---

## Step 2: Authenticate

```bash
epsimo auth
```

You'll be prompted for your email and password. If you don't have an account, the CLI will offer to create one.

Alternatively, set environment variables:

```bash
export EPSIMO_EMAIL=your@email.com
export EPSIMO_PASSWORD=your-password
epsimo auth
```

Verify you're logged in:

```bash
epsimo whoami
# Logged in as: your@email.com
# Threads Used: 0/100
```

---

## Step 3: Create a Project

### Option A: Scaffold a full Next.js app

```bash
epsimo create "My AI App"
cd my-ai-app
npm install
```

This creates a ready-to-run Next.js project with the Epsimo React UI Kit pre-configured.

### Option B: Initialize in an existing directory

```bash
cd my-existing-project
epsimo init
```

This creates an `epsimo.yaml` file and registers the project on the platform.

Either way, you'll get an `epsimo.yaml` like this:

```yaml
project_id: proj_abc123
name: My AI App
assistants:
  - name: default-assistant
    model: gpt-4o
    instructions: You are a helpful AI assistant created via the Epsimo CLI.
    tools:
      - type: retrieval
```

---

## Step 4: Deploy Your Configuration

Push the assistant configuration to the Epsimo platform:

```bash
epsimo deploy
```

Output:
```
🚀 Deploying configuration...
📦 Found 1 assistants in config.
✨ Creating assistant: default-assistant...
✅ Deployment complete!
```

---

## Step 5: Chat with Your Assistant

### Interactive chat

```bash
epsimo chat
```

The CLI auto-detects your project and assistant from `epsimo.yaml`. You'll see real-time streaming responses with tool call visibility.

### Simple run mode

```bash
epsimo run
```

Creates a new thread and opens a live chat. Type `exit` to quit.

### Specify project and assistant

```bash
epsimo run --project-id proj_abc123 --assistant-id asst_xyz789
```

---

## Step 6: Explore the TUI Dashboard

Launch the interactive terminal dashboard:

```bash
epsimo tui
```

Navigate with number keys `[1-6]` to switch between tabs:
- **Status** — Account info and balance
- **Projects** — Browse your projects
- **Assistants** — View and manage assistants
- **Threads** — List conversation threads
- **DB** — Inspect Virtual Database state
- **Tools** — Available tool types

Press `Q` to quit, `R` to refresh, `P` to switch projects.

---

## Step 7: Use the Virtual Database

The Virtual Database lets your assistant store structured data in thread state.

### Add the storage tool to your assistant

Edit `epsimo.yaml`:

```yaml
assistants:
  - name: default-assistant
    model: gpt-4o
    instructions: |
      You are a helpful assistant. Save important user information
      using the update_database tool.
    tools:
      - type: retrieval
      - type: function
        name: update_database
        description: "Persist structured data to thread state."
        parameters:
          type: object
          properties:
            key: { type: string }
            value: { type: object }
          required: ["key", "value"]
```

Redeploy:

```bash
epsimo deploy
```

### Query the database

```bash
# View all stored data
epsimo db query --project-id proj_abc --thread-id thread_123

# Set a value manually
epsimo db set --project-id proj_abc --thread-id thread_123 \
  --key "status" --value '"active"'
```

See [virtual_db_guide.md](virtual_db_guide.md) for the full guide.

---

## Step 8: Check Your Balance

```bash
epsimo credits balance
```

Output:
```
=== Thread Balance ===
Threads Used:      5
Total Allowance:   100
Threads Remaining: 95
======================
```

Need more threads?

```bash
epsimo credits buy --quantity 500
```

---

## What's Next?

- **[TUI Guide](tui-guide.md)** — Master the interactive dashboard
- **[Configuration Reference](configuration.md)** — Full `epsimo.yaml` schema
- **[Virtual DB Guide](virtual_db_guide.md)** — Thread-based storage patterns
- **[API Reference](../references/api_reference.md)** — REST API documentation
- **[Python SDK](../README.md#-python-sdk)** — Programmatic access

---

## Troubleshooting

### "Not logged in" error

```bash
epsimo auth          # Re-authenticate
epsimo auth --force  # Force re-authentication
```

### Token expired

Tokens expire after 1 hour. Run `epsimo auth` again, or set `EPSIMO_EMAIL` and `EPSIMO_PASSWORD` environment variables for automatic refresh.

### "No projects found"

```bash
epsimo init          # Create a project in the current directory
```

### Deploy fails

Make sure `epsimo.yaml` exists in the current directory and contains a valid `project_id`:

```bash
cat epsimo.yaml      # Check the file
epsimo deploy        # Try again
```
