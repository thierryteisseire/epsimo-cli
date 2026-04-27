# TUI Dashboard Guide

The Epsimo TUI (Terminal User Interface) is an interactive dashboard for managing your AI agents, projects, threads, and Virtual Database — all from the terminal.

---

## Launching the TUI

```bash
epsimo tui
```

You must be authenticated first (`epsimo auth`). The TUI connects to the Epsimo platform and loads your projects automatically.

---

## Main Menu

```
╔══════════════════════════════════════════════════════╗
║  ⚡ Epsimo Dashboard — Main Menu                    ║
╚══════════════════════════════════════════════════════╝

  Active project: My AI App

  1) Status        — Account info & thread usage
  2) Projects      — List & switch projects
  3) Assistants    — AI agents in current project
  4) Threads       — Conversations in current project
  5) Virtual DB    — Query thread state / data
  6) Tools         — Available backend tools
  7) Chat          — Start a conversation with an assistant
  8) New Assistant — Create an assistant (guided wizard)
  9) Buy Threads   — Purchase additional thread credits

  q) Quit
```

Navigate by pressing the number key for the screen you want.

---

## Screens

### 1. Status

Displays your account overview:
- Email address
- Threads used / total allowance
- Remaining threads
- Number of projects
- Active project name
- API base URL

Press `b` from this screen to jump to the Buy Threads flow.

### 2. Projects

Lists all your projects in a table with ID and name. If you have multiple projects, you can switch the active project here. The active project determines which assistants, threads, and DB data are shown in other screens.

### 3. Assistants

Lists all AI assistants in the current project. Shows:
- Assistant ID
- Name
- Model
- Tool count

Press `Enter` on an assistant to view its full configuration, including instructions and tool definitions.

### 4. Threads

Lists all conversation threads in the current project. Shows:
- Thread ID
- Name
- Assistant ID
- Creation date

### 5. Virtual DB

Query the structured state of any thread. Select a thread to view its key-value data as formatted JSON. This is the same data written by the `update_database` tool during conversations.

### 6. Tools

Lists all available tool types from the backend, including:
- Tool type name
- Description
- Health status

### 7. Chat

Opens an interactive chat session with an assistant. Features:
- Real-time streaming responses
- Tool call visualization with animated spinners
- Slash commands (see below)
- Auto-completion for slash commands

### 8. New Assistant (Wizard)

Guided wizard to create a new assistant:
1. Enter a name
2. Choose a model (gpt-4o, gpt-4o-mini, etc.)
3. Write system instructions
4. Select tools to enable
5. Set public/private visibility

### 9. Buy Threads

Generate a Stripe checkout URL to purchase additional thread credits. Shows current balance and pricing tiers before purchase.

---

## Slash Commands (Chat Mode)

When in the Chat screen, type `/` to see available commands with auto-completion:

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/status` | Display account info |
| `/credits` | Show thread balance |
| `/db` | View Virtual DB for current thread |
| `/db set` | Set a key-value pair in the DB |
| `/tools` | List available tools |
| `/threads` | List threads in current project |
| `/assistants` | List assistants in current project |
| `/switch` | Switch to a different assistant |
| `/create` | Launch the new assistant wizard |
| `/buy` | Purchase additional threads |
| `/clear` | Clear the screen |
| `/info` | Show current session info (project, assistant, thread IDs) |

### Slash Command Auto-completion

As you type a `/` command, matching commands appear as hints below the input line. Press `Tab` to auto-complete the first match.

---

## Animated Spinners

The TUI uses animated spinners to indicate background operations:

| Spinner | When It Appears |
|---------|----------------|
| ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏ | Connecting to API |
| 🧠💭✨ | Assistant is thinking |
| 🔍🔎 | Searching |
| ✍️📝 | Writing response |
| 🔧⚙️ | Tool call in progress |
| ◐◓◑◒ | Loading data |
| ▌▐ | Streaming response |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1`–`9` | Navigate to screen |
| `q` | Quit TUI / go back |
| `Enter` | Drill into selected item |
| `r` | Refresh current data |
| `p` | Switch active project |
| `b` | Buy threads (from Status screen) |
| `Tab` | Auto-complete slash commands |
| `Ctrl+C` | Exit |

---

## Tips

- **Project context matters** — Screens 3–5 (Assistants, Threads, DB) show data for the active project. Switch projects with option `2` or press `p`.
- **Use slash commands in chat** — They're faster than exiting chat to check status or switch assistants.
- **The TUI caches data** — Press `r` to refresh if you've made changes outside the TUI.
- **Works over SSH** — The TUI uses ANSI escape codes and works in any terminal that supports them.

---

## Troubleshooting

### "Not authenticated" error

```bash
epsimo auth
epsimo tui
```

### No projects shown

```bash
epsimo init          # Create a project first
epsimo tui
```

### Display issues

The TUI requires a terminal that supports ANSI escape codes. If you see garbled output:
- Try a different terminal emulator
- Ensure your terminal supports UTF-8
- Check that `TERM` is set (e.g., `xterm-256color`)
