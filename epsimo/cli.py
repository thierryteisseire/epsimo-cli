#!/usr/bin/env python3
import argparse
import sys
import os
import json
import yaml
from .client import EpsimoClient
from .auth import login_interactive, get_token
from .cli_smart import cmd_chat, cmd_exec, cmd_search, cmd_tools, cmd_tools_health
from .tui import cmd_tui

def cmd_whoami(args):
    """Show current user info."""
    print("👤 Fetching user info...")
    try:
        token = get_token()
        if not token:
            print("❌ Not logged in. Use 'epsimo auth'.")
            return
            
        client = EpsimoClient(api_key=token)
        # Using a guessed endpoint from auth scripts (thread-info is a proxy for profile info sometimes)
        # Or better check if there is a profile endpoint?
        # api.d.ts doesn't explicitly show /auth/whoami, but /auth/thread-info is available
        info = client.request("GET", "/auth/thread-info")
        print(f"Logged in as: {info.get('email', 'Unknown User')}")
        print(f"Threads Used: {info.get('thread_counter')}/{info.get('thread_max')}")
        
    except Exception as e:
        print(f"❌ Failed to fetch user info: {e}")

def cmd_balance(args):
    """Check the current thread and credit balance."""
    print("💳 Checking balance...")
    try:
        token = get_token()
        client = EpsimoClient(api_key=token)
        data = client.credits.get_balance()
        
        thread_count = data.get("thread_counter", 0)
        thread_max = data.get("thread_max", 0)
        remaining = thread_max - thread_count
        
        print("\n=== Thread Balance ===")
        print(f"Threads Used:      {thread_count}")
        print(f"Total Allowance:   {thread_max}")
        print(f"Threads Remaining: {remaining}")
        print("======================\n")
            
    except Exception as e:
        print(f"❌ Failed to check balance: {e}")

def cmd_buy(args):
    """Create a checkout session to buy credits."""
    print(f"🛒 Preparing purchase of {args.quantity} credits...")

    try:
        token = get_token()
        client = EpsimoClient(api_key=token)
        data = client.credits.create_checkout_session(args.quantity)
        
        checkout_url = data.get("url")
        if checkout_url:
            print("\n✅ Checkout session created!")
            print(f"Complete your purchase here:\n\n{checkout_url}\n")
        else:
            print("❌ No checkout URL returned from server.")
            
    except Exception as e:
        print(f"❌ Failed to create checkout session: {e}")

def cmd_auth(args):
    """Handle authentication."""
    print("🔐 Authenticating Epsimo CLI...")
    
    # Check if we should skip login if already valid
    token = get_token()
    if token and not args.force:
        print("✅ Already logged in. Use 'epsimo auth --force' to re-authenticate.")
        return
    
    try:
        login_interactive()
        token = get_token()
        if token:
            print(f"✅ Successfully logged in!")
        else:
            print("❌ Login failed (no token found).")
    except Exception as e:
        print(f"❌ Error during auth: {e}")

def cmd_projects(args):
    """List projects."""
    if not args.json:
        print("📁 Fetching projects...")
    try:
        token = get_token()
        client = EpsimoClient(api_key=token)
        projects = client.projects.list()
        
        if args.json:
            print(json.dumps(projects))
            return

        if not projects:
            print("No projects found.")
            return
            
        print(f"{'ID':<40} | {'Name':<20}")
        print("-" * 65)
        for p in projects:
            print(f"{p['project_id']:<40} | {p['name']:<20}")
            
    except Exception as e:
        if not args.json:
            print(f"❌ Failed to fetch projects: {e}")
        else:
            print(json.dumps({"error": str(e)}))

def cmd_assistants(args):
    """List assistants in a project."""
    if not args.json:
        print(f"🤖 Fetching assistants for project {args.project_id}...")
    try:
        token = get_token()
        client = EpsimoClient(api_key=token)
        assistants = client.assistants.list(args.project_id)
        
        if args.json:
            print(json.dumps(assistants))
            return

        if not assistants:
            print("No assistants found.")
            return
            
        print(f"{'ID':<40} | {'Name':<20}")
        print("-" * 65)
        for a in assistants:
            print(f"{a['assistant_id']:<40} | {a['name']:<20}")
            
    except Exception as e:
        if not args.json:
            print(f"❌ Failed to fetch assistants: {e}")
        else:
            print(json.dumps({"error": str(e)}))

def cmd_threads(args):
    """List threads in a project."""
    print(f"🧵 Fetching threads for project {args.project_id}...")
    try:
        token = get_token()
        client = EpsimoClient(api_key=token)
        threads = client.threads.list(args.project_id)
        
        if not threads:
            print("No threads found.")
            return
            
        print(f"{'ID':<40} | {'Name':<20}")
        print("-" * 65)
        for t in threads:
            print(f"{t['thread_id']:<40} | {t['name']:<20}")
            
    except Exception as e:
        print(f"❌ Failed to fetch threads: {e}")

def cmd_init(args):
    """Initialize a new Epsimo project in the current directory."""
    print("🚀 Initializing Epsimo project...")
    
    if os.path.exists("epsimo.yaml"):
        print("⚠️  epsimo.yaml already exists in this directory.")
        choice = input("Do you want to overwrite it? (y/n): ")
        if choice.lower() != 'y':
            return

    # 1. Auth & Client
    try:
        token = get_token()
        if not token:
            print("🔐 Authentication required.")
            login_interactive()
            token = get_token()
        
        client = EpsimoClient(api_key=token)
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return

    # 2. Project Selection/Creation
    project_name = args.name or os.path.basename(os.getcwd())
    print(f"📁 Project Name: {project_name}")
    
    try:
        print("Creating project on Epsimo platform...")
        project = client.projects.create(name=project_name)
        project_id = project["project_id"]
        print(f"✅ Project Created: {project_id}")
    except Exception as e:
        print(f"❌ Failed to create project: {e}")
        return

    # 3. Generate epsimo.yaml
    config = {
        "project_id": project_id,
        "name": project_name,
        "assistants": [
            {
                "name": "default-assistant",
                "model": "gpt-4o",
                "instructions": "You are a helpful AI assistant created via the Epsimo CLI.",
                "tools": [
                    {"type": "retrieval"}
                ]
            }
        ]
    }
    
    try:
        with open("epsimo.yaml", "w") as f:
            yaml.dump(config, f, sort_keys=False)
        print("✅ Created epsimo.yaml")
        print("\nNext steps:")
        print("1. Edit epsimo.yaml to configure your assistants.")
        print(f"2. Run 'epsimo deploy' to sync changes (coming soon).")
        print(f"3. Chat with your assistant: 'epsimo run --project-id {project_id} --assistant-id <ID>'")
    except Exception as e:
        print(f"❌ Failed to write epsimo.yaml: {e}")

def cmd_deploy(args):
    """Deploy configuration from epsimo.yaml to the platform."""
    print("🚀 Deploying configuration...")
    
    if not os.path.exists("epsimo.yaml"):
        print("❌ epsimo.yaml not found. Run 'epsimo init' first.")
        return

    # 1. Load config
    try:
        with open("epsimo.yaml", "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load epsimo.yaml: {e}")
        return

    project_id = config.get("project_id")
    if not project_id:
        print("❌ project_id missing in epsimo.yaml")
        return

    # 2. Auth & Client
    try:
        token = get_token()
        client = EpsimoClient(api_key=token)
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return

    # 3. Process Assistants
    assistants_config = config.get("assistants", [])
    print(f"📦 Found {len(assistants_config)} assistants in config.")
    
    try:
        # Fetch current assistants to match by name
        current_assistants = client.assistants.list(project_id)
        asst_map = {a["name"]: a for a in current_assistants}
        
        for asst_cfg in assistants_config:
            name = asst_cfg.get("name")
            if not name: continue
            
            model = asst_cfg.get("model", "gpt-4o")
            instructions = asst_cfg.get("instructions", "")
            tools = asst_cfg.get("tools", [])
            
            if name in asst_map:
                asst_id = asst_map[name]["assistant_id"]
                print(f"🔄 Updating assistant: {name} ({asst_id})...")
                # Prepare payload using the same logic as create
                payload = client.assistants._prepare_payload(
                    name=name,
                    model=model,
                    instructions=instructions,
                    tools=tools,
                    public=asst_map[name].get("public", False)
                )
                client.assistants.update(project_id, asst_id, payload)
            else:
                print(f"✨ Creating assistant: {name}...")
                client.assistants.create(
                    project_id=project_id,
                    name=name,
                    model=model,
                    instructions=instructions,
                    tools=tools
                )
        
        print("✅ Deployment complete!")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")

def cmd_db(args):
    """Query the structured state (virtual database) of a thread."""
    print(f"📊 Querying Virtual Database for thread {args.thread_id}...")
    try:
        token = get_token()
        client = EpsimoClient(api_key=token)
        state = client.threads.get_state(args.project_id, args.thread_id)
        
        # The state typically has 'values' which is our DB
        values = state.get("values", {})
        
        if not values:
            print("📭 Database is empty.")
            return
            
        print("\n=== Current State (JSON) ===")
        print(json.dumps(values, indent=2))
        print("============================\n")
            
    except Exception as e:
        print(f"❌ Failed to query database: {e}")

def cmd_db_set(args):
    """Set a value in the thread's virtual database."""
    print(f"📝 Setting {args.key} = {args.value} in thread {args.thread_id}...")
    try:
        # Parse value as JSON if possible, otherwise keep as string
        try:
            val = json.loads(args.value)
        except:
            val = args.value
            
        token = get_token()
        client = EpsimoClient(api_key=token)
        client.threads.set_state(args.project_id, args.thread_id, {args.key: val})
        print("✅ State updated successfully.")
            
    except Exception as e:
        print(f"❌ Failed to update database: {e}")

def cmd_create(args):
    """Scaffold a new Epsimo MVP project."""
    project_name = args.name
    project_slug = project_name.lower().replace(" ", "-")
    target_dir = os.path.abspath(project_slug)
    
    print(f"🏗️  Creating new Epsimo MVP project: {project_name}...")
    
    if os.path.exists(target_dir):
        print(f"❌ Directory {project_slug} already exists.")
        return

    # Path to templates inside the skill
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "templates", "next-mvp")
    
    if not os.path.exists(template_dir):
        print(f"❌ Template directory not found at {template_dir}")
        return

    try:
        os.makedirs(target_dir)
        
        # 1. Walk through template dir and copy/transform files
        for root, dirs, files in os.walk(template_dir):
            rel_path = os.path.relpath(root, template_dir)
            
            # Create subdirectories
            for d in dirs:
                os.makedirs(os.path.join(target_dir, rel_path, d), exist_ok=True)
            
            # Copy files
            for f in files:
                if not f.endswith(".tmpl"): continue
                
                src_path = os.path.join(root, f)
                dest_filename = f.replace(".tmpl", "")
                dest_path = os.path.join(target_dir, rel_path, dest_filename)
                
                with open(src_path, "r") as src_f:
                    content = src_f.read()
                
                # Replace placeholders
                content = content.replace("{{PROJECT_NAME}}", project_name)
                content = content.replace("{{PROJECT_SLUG}}", project_slug)
                content = content.replace("{{ASSISTANT_ID}}", "TODO_DEPLOY_FIRST")
                
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "w") as dest_f:
                    dest_f.write(content)

        # 2. Copy the UI components from the current codebase to the new project
        # In a real framework, this would be an npm install @epsimo/ui
        # For this MVP, we copy the files.
        print("📦 Injecting Epsimo UI Kit...")
        # Since we are in the context of the current repo:
        src_ui_dir = "/Users/thierry/code/epsimo-frontend/src/components/epsimo"
        dest_ui_dir = os.path.join(target_dir, "components", "epsimo")
        
        import shutil
        if os.path.exists(src_ui_dir):
            shutil.copytree(src_ui_dir, dest_ui_dir, dirs_exist_ok=True)
        
        print(f"\n✅ Project {project_name} created successfully at ./{project_slug}")
        print("\nNext steps:")
        print(f"1. cd {project_slug}")
        print("2. npm install")
        print("3. epsimo init (to link to platform)")
        print("4. epsimo deploy (to create assistants)")
        print("5. npm run dev")
        
    except Exception as e:
        print(f"❌ Failed to create project: {e}")

def _pick_item(items, label, name_key="name"):
    """Prompt user to pick from a list. Auto-selects if only one."""
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
            return None
        print(f"  Invalid choice. Enter 1-{len(items)}.")


def cmd_run(args):
    """Run an interactive chat with an assistant."""
    # 1. Initialize Client
    try:
        token = get_token()
        client = EpsimoClient(api_key=token)
    except Exception as e:
        print(f"❌ Auth failed: {e}. Try 'epsimo auth'.")
        return

    # 2. Resolve project
    project_id = getattr(args, "project_id", None)
    if not project_id:
        projects = client.projects.list()
        if not projects:
            print("❌ No projects found. Run 'epsimo init' to create one.")
            return
        picked = _pick_item(projects, "project")
        if not picked:
            return
        project_id = picked["project_id"]

    # 3. Resolve assistant
    assistant_id = getattr(args, "assistant_id", None)
    if not assistant_id:
        assistants = client.assistants.list(project_id)
        if not assistants:
            print("❌ No assistants found in this project.")
            return
        picked = _pick_item(assistants, "assistant")
        if not picked:
            return
        assistant_id = picked["assistant_id"]

    print(f"▶️  Running Assistant: {assistant_id[:8]}…")

    # 4. Create Thread
    print("🧵 Creating session thread...")
    try:
        thread = client.threads.create(project_id, "CLI Session", assistant_id)
        thread_id = thread["thread_id"]
    except Exception as e:
        print(f"❌ Failed to create thread: {e}")
        return

    # 5. Chat Loop
    print(f"✅ Ready! (Thread: {thread_id})")
    print("Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("You > ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            print("Bot > ", end="", flush=True)
            stream = client.threads.run_stream(
                project_id=project_id,
                thread_id=thread_id,
                assistant_id=assistant_id,
                message=user_input
            )
            
            last_printed_len = 0
            spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            spin_idx = 0
            active_tool = None
            seen_tool_ids = set()
            for chunk in stream:
                if not isinstance(chunk, list) or len(chunk) != 1:
                    continue
                item = chunk[0]
                if not isinstance(item, dict):
                    continue
                msg_type = item.get("type", "")
                msg_id = item.get("id") or item.get("tool_call_id", "")

                # Tool response — show result once
                if msg_type == "tool":
                    if msg_id and msg_id in seen_tool_ids:
                        continue
                    if msg_id:
                        seen_tool_ids.add(msg_id)
                    if active_tool:
                        content = item.get("content", "")
                        result = str(content)[:500] if content else ""
                        sys.stdout.write(f"\r✅ {active_tool} done          \n")
                        if result.strip():
                            sys.stdout.write(f"   📎 {result.strip()}\n")
                        sys.stdout.flush()
                        active_tool = None
                        last_printed_len = 0
                    continue

                if msg_type not in ("ai", "AIMessageChunk"):
                    continue

                # Detect tool calls (only before tool result)
                tool_calls = item.get("tool_calls", [])
                if tool_calls and not seen_tool_ids:
                    for tc in tool_calls:
                        name = tc.get("name", "")
                        if name and name != active_tool:
                            active_tool = name
                    spin_idx = (spin_idx + 1) % len(spinner)
                    sys.stdout.write(f"\r{spinner[spin_idx]} Calling {active_tool}...")
                    sys.stdout.flush()
                    continue
                elif tool_calls and seen_tool_ids:
                    # After tool result, skip replayed tool_call chunks with no content
                    content = item.get("content")
                    if not content:
                        continue

                content = item.get("content")
                if content and isinstance(content, str):
                    new_text = content[last_printed_len:]
                    if new_text:
                        sys.stdout.write(new_text)
                        sys.stdout.flush()
                        last_printed_len = len(content)

                content = item.get("content")
                if content and isinstance(content, str):
                    new_text = content[last_printed_len:]
                    if new_text:
                        sys.stdout.write(new_text)
                        sys.stdout.flush()
                        last_printed_len = len(content)
            print("\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break

def main():
    F = argparse.RawDescriptionHelpFormatter

    parser = argparse.ArgumentParser(
        description="Epsimo Agent Framework CLI — build and manage AI-powered applications",
        formatter_class=F,
        epilog="""quick start:
  epsimo auth                  Log in to your account
  epsimo create "My AI App"    Scaffold a new project
  cd my-ai-app && epsimo init  Link directory to platform
  epsimo deploy                Push config to Epsimo cloud

docs: https://github.com/thierryteisseire/epsimo-agent"""
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # epsimo init
    init_parser = subparsers.add_parser("init",
        help="Link current directory to a new Epsimo project on the platform",
        formatter_class=F,
        epilog="""examples:
  epsimo init                  Use current directory name as project name
  epsimo init --name "My Bot"  Use a custom project name

Creates epsimo.yaml with project config and a default assistant.""")
    init_parser.add_argument("--name", help="Project name (defaults to current directory name)")
    init_parser.set_defaults(func=cmd_init)

    # epsimo deploy
    deploy_parser = subparsers.add_parser("deploy",
        help="Sync local epsimo.yaml configuration to the Epsimo platform",
        formatter_class=F,
        epilog="""examples:
  epsimo deploy                Push assistants and config to the cloud

Reads epsimo.yaml from the current directory. Creates new assistants
or updates existing ones that match by name.""")
    deploy_parser.set_defaults(func=cmd_deploy)

    # epsimo create
    create_parser = subparsers.add_parser("create",
        help="Scaffold a new Next.js project with Epsimo UI Kit pre-configured",
        formatter_class=F,
        epilog="""examples:
  epsimo create "Customer Support Bot"
  epsimo create "Research Assistant"

Creates a ready-to-run Next.js app with chat UI, streaming, and
Virtual Database integration. Follow up with: cd <project> && npm install""")
    create_parser.add_argument("name", help="Display name for the new project (e.g. \"My AI App\")")
    create_parser.set_defaults(func=cmd_create)

    # epsimo auth
    auth_parser = subparsers.add_parser("auth",
        help="Authenticate with your Epsimo account (interactive email/password login)",
        formatter_class=F,
        epilog="""examples:
  epsimo auth                  Interactive login prompt
  epsimo auth --force          Re-authenticate even if already logged in

You can also set EPSIMO_EMAIL and EPSIMO_PASSWORD environment variables.""")
    auth_parser.add_argument("--force", action="store_true",
        help="Force re-authentication even if a valid token exists")
    auth_parser.set_defaults(func=cmd_auth)

    # epsimo whoami
    whoami_parser = subparsers.add_parser("whoami",
        help="Display your login email and current thread usage",
        formatter_class=F,
        epilog="""examples:
  epsimo whoami

output:
  Logged in as: user@example.com
  Threads Used: 45/100""")
    whoami_parser.set_defaults(func=cmd_whoami)

    # epsimo projects
    projects_parser = subparsers.add_parser("projects",
        help="List all projects in your account",
        formatter_class=F,
        epilog="""examples:
  epsimo projects              Show projects as a table
  epsimo projects --json       Output as JSON (for scripting)""")
    projects_parser.add_argument("--json", action="store_true",
        help="Output project list as JSON instead of a table")
    projects_parser.set_defaults(func=cmd_projects)

    # epsimo credits {balance, buy}
    credits_parser = subparsers.add_parser("credits",
        help="Check thread balance or purchase additional threads",
        formatter_class=F,
        epilog="""examples:
  epsimo credits balance       Show threads used/remaining
  epsimo credits buy --quantity 500""")
    credits_subparsers = credits_parser.add_subparsers(dest="credits_command", help="Credits action")

    balance_parser = credits_subparsers.add_parser("balance",
        help="Show current thread usage, total allowance, and remaining threads")
    balance_parser.set_defaults(func=cmd_balance)

    buy_parser = credits_subparsers.add_parser("buy",
        help="Generate a Stripe checkout URL to purchase additional threads")
    buy_parser.add_argument("--quantity", type=int, required=True,
        help="Number of threads to purchase (e.g. 500, 1000)")
    buy_parser.set_defaults(func=cmd_buy)

    # epsimo assistants --project-id X
    assistants_parser = subparsers.add_parser("assistants",
        help="List all AI assistants in a project",
        formatter_class=F,
        epilog="""examples:
  epsimo assistants --project-id proj_abc123
  epsimo assistants --project-id proj_abc123 --json""")
    assistants_parser.add_argument("--project-id", required=True,
        help="ID of the project to list assistants from (see 'epsimo projects')")
    assistants_parser.add_argument("--json", action="store_true",
        help="Output assistant list as JSON instead of a table")
    assistants_parser.set_defaults(func=cmd_assistants)

    # epsimo threads --project-id X
    threads_parser = subparsers.add_parser("threads",
        help="List all conversation threads in a project",
        formatter_class=F,
        epilog="""examples:
  epsimo threads --project-id proj_abc123""")
    threads_parser.add_argument("--project-id", required=True,
        help="ID of the project to list threads from (see 'epsimo projects')")
    threads_parser.set_defaults(func=cmd_threads)

    # epsimo run --project-id X --assistant-id Y
    run_parser = subparsers.add_parser("run",
        help="Start an interactive terminal chat session with an assistant",
        formatter_class=F,
        epilog="""examples:
  epsimo run                                     Auto-select project and assistant
  epsimo run --project-id proj_abc123            Pick assistant interactively
  epsimo run --project-id proj_abc --assistant-id asst_xyz

Creates a new thread and opens a live chat. Type 'exit' to quit.""")
    run_parser.add_argument("--project-id",
        help="Project ID (omit to choose interactively)")
    run_parser.add_argument("--assistant-id",
        help="Assistant ID (omit to choose interactively)")
    run_parser.set_defaults(func=cmd_run)

    # epsimo db query --project-id X --thread-id Y
    db_parser = subparsers.add_parser("db",
        help="Read and write structured data in the Virtual Database (thread state)",
        formatter_class=F,
        epilog="""examples:
  epsimo db query --project-id proj_abc --thread-id thread_123
  epsimo db set --project-id proj_abc --thread-id thread_123 \\
    --key "status" --value '"completed"'

The Virtual Database stores persistent key-value data per thread.""")
    db_subparsers = db_parser.add_subparsers(dest="db_command", help="Virtual Database action")

    query_parser = db_subparsers.add_parser("query",
        help="Display all stored key-value pairs for a thread")
    query_parser.add_argument("--project-id", required=True,
        help="ID of the project containing the thread")
    query_parser.add_argument("--thread-id", required=True,
        help="ID of the thread to query state from")
    query_parser.set_defaults(func=cmd_db)

    set_parser = db_subparsers.add_parser("set",
        help="Write or update a key-value pair in a thread's state")
    set_parser.add_argument("--project-id", required=True,
        help="ID of the project containing the thread")
    set_parser.add_argument("--thread-id", required=True,
        help="ID of the thread to update")
    set_parser.add_argument("--key", required=True,
        help="Key name to set (e.g. \"user_preferences\", \"status\")")
    set_parser.add_argument("--value", required=True,
        help="Value to store — supports JSON (e.g. '\"done\"', '{\"a\":1}')")
    set_parser.set_defaults(func=cmd_db_set)

    # --- Smart Commands (cli_smart.py) ---

    # Helper to add common smart-command args
    def _add_smart_args(p):
        p.add_argument("--project-id",
            help="Project ID (default: read from epsimo.yaml in current directory)")
        p.add_argument("--assistant-id",
            help="Assistant ID (default: auto-detected from project)")
        p.add_argument("--base-url",
            help="Backend API URL override (e.g. http://localhost:8000)")

    # epsimo chat
    chat_parser = subparsers.add_parser("chat",
        help="Interactive chat with real-time tool call visibility",
        formatter_class=F,
        epilog="""examples:
  epsimo chat                                    Auto-detect project/assistant
  epsimo chat --tools search_tavily,ddg_search   Enable specific tools
  epsimo chat --base-url http://localhost:8000    Use local backend

Like 'run' but shows when the assistant calls tools in real time.""")
    _add_smart_args(chat_parser)
    chat_parser.add_argument("--tools",
        help="Comma-separated tool types to enable (e.g. search_tavily,dall_e)")
    chat_parser.set_defaults(func=cmd_chat)

    # epsimo exec
    exec_parser = subparsers.add_parser("exec",
        help="Send code to a backend assistant for execution",
        formatter_class=F,
        epilog="""examples:
  epsimo exec "print('Hello world')"
  epsimo exec --file script.py
  epsimo exec "2 + 2" --base-url http://localhost:8000""")
    exec_parser.add_argument("code", nargs="?", default=None,
        help="Python code string to execute (e.g. \"print('hello')\")")
    exec_parser.add_argument("--file",
        help="Path to a code file to execute instead of inline code")
    _add_smart_args(exec_parser)
    exec_parser.set_defaults(func=cmd_exec)

    # epsimo search
    search_parser = subparsers.add_parser("search",
        help="Perform a web search through a backend assistant",
        formatter_class=F,
        epilog="""examples:
  epsimo search "latest AI news"
  epsimo search "Python async patterns" --tool search_tavily
  epsimo search "Docker best practices" --tool ddg_search""")
    search_parser.add_argument("query", help="Search query text (e.g. \"LangChain agents\")")
    search_parser.add_argument("--tool", default="search_tavily",
        help="Search provider: search_tavily (default) or ddg_search")
    _add_smart_args(search_parser)
    search_parser.set_defaults(func=cmd_search)

    # epsimo tools [list | health <type>]
    tools_parser = subparsers.add_parser("tools",
        help="List available tools or check their health status",
        formatter_class=F,
        epilog="""examples:
  epsimo tools                           List all available tools
  epsimo tools --json                    Output tool list as JSON
  epsimo tools health ddg_search         Check if DuckDuckGo search is working
  epsimo tools health search_tavily      Check Tavily search health""")
    tools_parser.add_argument("--base-url",
        help="Backend API URL override (e.g. http://localhost:8000)")
    tools_parser.add_argument("--json", action="store_true",
        help="Output tool list as JSON instead of a table")
    tools_subparsers = tools_parser.add_subparsers(dest="tools_command")
    tools_parser.set_defaults(func=cmd_tools)

    tools_health_parser = tools_subparsers.add_parser("health",
        help="Run a health check on a specific tool to verify it is working")
    tools_health_parser.add_argument("tool_type",
        help="Tool type to check (e.g. ddg_search, search_tavily, dall_e)")
    tools_health_parser.add_argument("--json", action="store_true",
        help="Output health check result as JSON")
    tools_health_parser.add_argument("--base-url",
        help="Backend API URL override (e.g. http://localhost:8000)")
    tools_health_parser.set_defaults(func=cmd_tools_health)

    # epsimo tui
    tui_parser = subparsers.add_parser("tui",
        help="Launch an interactive terminal dashboard with live data",
        formatter_class=F,
        epilog="""examples:
  epsimo tui

Navigate with arrow keys or number keys [1-6] to switch tabs.
Tabs: Status, Projects, Assistants, Threads, DB, Tools.
Press [P] to switch project, [R] to refresh, [Enter] to drill in, [Q] to quit.""")
    tui_parser.set_defaults(func=cmd_tui)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
