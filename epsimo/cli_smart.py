#!/usr/bin/env python3
"""Smart CLI commands: chat, exec, search, tools."""
import sys
import os
import json
import yaml
from .client import EpsimoClient
from .auth import get_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(args):
    """Build an EpsimoClient, honouring --base-url."""
    token = get_token()
    if not token:
        print("❌ Not logged in. Run 'epsimo auth' first.")
        sys.exit(1)
    base_url = getattr(args, "base_url", None)
    return EpsimoClient(api_key=token, base_url=base_url)


def _load_yaml_config():
    """Load epsimo.yaml from cwd (if present)."""
    if os.path.exists("epsimo.yaml"):
        with open("epsimo.yaml") as f:
            return yaml.safe_load(f)
    return None


def _pick(items, label, name_key="name", id_key=None):
    """Prompt user to pick from a list. Returns the chosen item dict."""
    if not items:
        return None
    if len(items) == 1:
        print(f"📌 Using {label}: {items[0].get(name_key, '?')}")
        return items[0]
    print(f"\n  Select a {label}:")
    for i, item in enumerate(items, 1):
        print(f"  {i}) {item.get(name_key, '?')}")
    while True:
        try:
            choice = input(f"  Enter number [1-{len(items)}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return items[idx]
        except (ValueError, EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        print(f"  Invalid choice. Enter 1-{len(items)}.")


def _get_smart_context(args, tool_overrides=None):
    """
    Resolve project / assistant / thread from epsimo.yaml + args.

    Returns dict with keys: client, project_id, assistant_id, thread_id
    """
    client = _make_client(args)
    cfg = _load_yaml_config()

    # --- project ---
    project_id = getattr(args, "project_id", None)
    if not project_id and cfg:
        project_id = cfg.get("project_id")
    if not project_id:
        projects = client.projects.list()
        if not projects:
            print("❌ No projects found. Run 'epsimo init' to create one.")
            sys.exit(1)
        picked = _pick(projects, "project")
        project_id = picked["project_id"]

    # --- assistant ---
    assistant_id = getattr(args, "assistant_id", None)
    if not assistant_id:
        if tool_overrides:
            asst = client.assistants.create(
                project_id=project_id,
                name="CLI Smart Assistant",
                instructions="You are a helpful AI assistant. Use your tools when needed to answer questions accurately.",
                tools=tool_overrides,
            )
            assistant_id = asst["assistant_id"]
        else:
            assistants = client.assistants.list(project_id)
            if assistants:
                picked = _pick(assistants, "assistant")
                assistant_id = picked["assistant_id"]
            else:
                asst = client.assistants.create(
                    project_id=project_id,
                    name="CLI Smart Assistant",
                    instructions="You are a helpful AI assistant with access to web search and document retrieval tools. Use them when needed.",
                    tools=[
                        {"type": "search_tavily"},
                        {"type": "ddg_search"},
                        {"type": "retrieval"},
                    ],
                )
                assistant_id = asst["assistant_id"]
                print(f"✨ Created assistant: CLI Smart Assistant ({assistant_id})")

    # --- thread ---
    thread = client.threads.create(project_id, "CLI Session", assistant_id)
    thread_id = thread["thread_id"]

    return {
        "client": client,
        "project_id": project_id,
        "assistant_id": assistant_id,
        "thread_id": thread_id,
    }


def _stream_response(ctx, message):
    """Stream a run and print response with inline tool-call display.

    Returns the full accumulated text.
    """
    full_text = ""
    last_len = 0
    spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    spin_idx = 0
    active_tool = None
    for chunk in ctx["client"].threads.run_stream(
        ctx["project_id"], ctx["thread_id"], ctx["assistant_id"], message
    ):
        if not isinstance(chunk, list) or len(chunk) != 1:
            continue
        item = chunk[0]
        if not isinstance(item, dict):
            continue
        msg_type = item.get("type", "")

        if msg_type == "tool":
            if active_tool:
                content = item.get("content", "")
                result = str(content)[:500] if content else ""
                sys.stdout.write(f"\r✅ {active_tool} done          \n")
                if result.strip():
                    sys.stdout.write(f"   📎 {result.strip()}\n")
                sys.stdout.flush()
                active_tool = None
                last_len = 0
            continue

        if msg_type not in ("ai", "AIMessageChunk"):
            continue

        tool_calls = item.get("tool_calls", [])
        if tool_calls:
            for tc in tool_calls:
                name = tc.get("name", "")
                if name and name != active_tool:
                    active_tool = name
            spin_idx = (spin_idx + 1) % len(spinner)
            sys.stdout.write(f"\r{spinner[spin_idx]} Calling {active_tool}...")
            sys.stdout.flush()
            continue

        content = item.get("content")
        if content and isinstance(content, str):
            new = content[last_len:]
            if new:
                sys.stdout.write(new)
                sys.stdout.flush()
                last_len = len(content)
                full_text = content
    return full_text


# ---------------------------------------------------------------------------
# cmd_tools  /  cmd_tools_health
# ---------------------------------------------------------------------------

def cmd_tools(args):
    """List available tools from the backend."""
    client = _make_client(args)
    try:
        data = client.request("GET", "/tools/")
    except Exception as e:
        print(f"❌ Failed to list tools: {e}")
        return

    tools = data.get("tools", data) if isinstance(data, dict) else data

    if getattr(args, "json", False):
        print(json.dumps(tools, indent=2))
        return

    print(f"\n{'Name':<25} {'Type':<25} {'Description'}")
    print("-" * 80)
    for t in (tools if isinstance(tools, list) else []):
        print(f"{t.get('name','?'):<25} {t.get('type','?'):<25} {t.get('description','')[:40]}")
    print()


def cmd_tools_health(args):
    """Check health of a specific tool."""
    client = _make_client(args)
    try:
        data = client.request("GET", f"/health/tool/{args.tool_type}")
    except Exception as e:
        print(f"❌ Failed to check tool health: {e}")
        return

    if getattr(args, "json", False):
        print(json.dumps(data, indent=2))
        return

    status = data.get("status", "unknown")
    icon = "✅" if status == "healthy" else "❌"
    print(f"{icon} {args.tool_type}: {status}")
    if data.get("message"):
        print(f"   {data['message']}")
    if data.get("error"):
        print(f"   Error: {data['error']}")


# ---------------------------------------------------------------------------
# cmd_search
# ---------------------------------------------------------------------------

def cmd_search(args):
    """Web search via backend assistant."""
    tool_type = getattr(args, "tool", "search_tavily")
    ctx = _get_smart_context(args, tool_overrides=[{"type": tool_type}])

    query = args.query
    print(f"🔍 Searching: {query}\n")
    _stream_response(ctx, f"Search the web for: {query}")
    print("\n")


# ---------------------------------------------------------------------------
# cmd_chat
# ---------------------------------------------------------------------------

def cmd_chat(args):
    """Smart interactive chat with tool visibility."""
    tools_csv = getattr(args, "tools", None)
    tool_overrides = None
    if tools_csv:
        tool_overrides = [{"type": t.strip()} for t in tools_csv.split(",")]

    ctx = _get_smart_context(args, tool_overrides=tool_overrides)
    print(f"💬 Chat ready (project={ctx['project_id'][:8]}… assistant={ctx['assistant_id'][:8]}…)")
    print("Type /exit to quit, /tools to list tools.\n")

    while True:
        try:
            user_input = input("You > ")
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input.strip():
            continue
        if user_input.strip() == "/exit":
            break
        if user_input.strip() == "/tools":
            # Quick inline tool list
            try:
                data = ctx["client"].request("GET", "/tools/")
                tools = data.get("tools", data) if isinstance(data, dict) else data
                for t in (tools if isinstance(tools, list) else []):
                    print(f"  • {t.get('name','?')} ({t.get('type','?')})")
            except Exception as e:
                print(f"  ❌ {e}")
            continue

        print("Bot > ", end="", flush=True)
        _stream_response(ctx, user_input)
        print("\n")

    print("👋 Bye!")


# ---------------------------------------------------------------------------
# cmd_exec
# ---------------------------------------------------------------------------

def cmd_exec(args):
    """Execute code via backend assistant."""
    code = args.code
    if getattr(args, "file", None):
        with open(args.file) as f:
            code = f.read()

    if not code:
        print("❌ No code provided. Pass code as argument or use --file.")
        return

    ctx = _get_smart_context(args)
    print(f"⚡ Executing code…\n")
    prompt = (
        "Execute the following code and return ONLY the output. "
        "If you cannot execute it, explain what it does and what the expected output would be.\n\n"
        f"```python\n{code}\n```"
    )
    _stream_response(ctx, prompt)
    print("\n")
