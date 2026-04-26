#!/usr/bin/env python3
import argparse
import sys
import os
import json
import yaml
from .client import EpsimoClient
from .auth import login_interactive, get_token

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
    print(f"🛒 Preparing purchase of {args.quantity} threads...")
    
    quantity = args.quantity
    total_amount = args.amount
    
    # Estimation logic if amount not provided
    if total_amount is None:
        if quantity >= 1000:
            price_per_unit = 0.08
        elif quantity >= 500:
            price_per_unit = 0.09
        else:
            price_per_unit = 0.10
        total_amount = round(quantity * price_per_unit, 2)
        print(f"ℹ️  Estimated cost: {total_amount} EUR")

    try:
        token = get_token()
        client = EpsimoClient(api_key=token)
        data = client.credits.create_checkout_session(quantity, total_amount)
        
        checkout_url = data.get("url")
        if checkout_url:
            print("\n✅ Checkout session created successfully!")
            print(f"Please visit this URL to complete your purchase:\n\n{checkout_url}\n")
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

def cmd_run(args):
    """Run an interactive chat with an assistant."""
    print(f"▶️  Running Assistant: {args.assistant_id}")
    
    # 1. Initialize Client
    try:
        client = EpsimoClient() # Auto-loads token from file via get_token in auth logic if not passed, 
                                # BUT client.py currently expects api_key env var or arg.
                                # Let's update client to try get_token if nothing passed?
                                # For now, explicit:
        token = get_token()
        client = EpsimoClient(api_key=token)
    except Exception as e:
        print(f"❌ Auth failed: {e}. Try 'epsimo auth'.")
        return

    # 2. Verify Assistant Exists (and get project context implicitly?)
    # We need a project_id to run things. 
    # CLI args should probably include project_id or we find the assistant.
    # Finding assistant across all projects is hard without a "search" endpoint.
    
    if not args.project_id:
        print("❌ --project-id is currently required.")
        return

    # 3. Create Thread
    print("🧵 Creating session thread...")
    try:
        thread = client.threads.create(args.project_id, "CLI Session", args.assistant_id)
        thread_id = thread["thread_id"]
    except Exception as e:
        print(f"❌ Failed to create thread: {e}")
        return

    # 4. Chat Loop
    print(f"✅ Ready! (Thread: {thread_id})")
    print("Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("You > ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            print("Bot > ", end="", flush=True)
            stream = client.threads.run_stream(
                project_id=args.project_id,
                thread_id=thread_id,
                assistant_id=args.assistant_id,
                message=user_input
            )
            
            last_printed_len = 0
            for chunk in stream:
                 # Handle both list and dict chunks as discovered in testing
                content = None
                if isinstance(chunk, list):
                    for item in chunk:
                        if isinstance(item, dict) and "content" in item:
                            content = item["content"]
                            break
                elif isinstance(chunk, dict) and "content" in chunk:
                    content = chunk["content"]
                
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
    parser = argparse.ArgumentParser(description="Epsimo Agent Framework CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # epsimo init
    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.add_argument("--name", help="Project name (defaults to current directory)")
    init_parser.set_defaults(func=cmd_init)

    # epsimo deploy
    deploy_parser = subparsers.add_parser("deploy", help="Deploy config from epsimo.yaml")
    deploy_parser.set_defaults(func=cmd_deploy)

    # epsimo create
    create_parser = subparsers.add_parser("create", help="Create a new Epsimo MVP project")
    create_parser.add_argument("name", help="Name of the project")
    create_parser.set_defaults(func=cmd_create)

    # epsimo auth
    auth_parser = subparsers.add_parser("auth", help="Login to Epsimo")
    auth_parser.add_argument("--force", action="store_true", help="Force re-authentication")
    auth_parser.set_defaults(func=cmd_auth)

    # epsimo whoami
    whoami_parser = subparsers.add_parser("whoami", help="Show current user info")
    whoami_parser.set_defaults(func=cmd_whoami)

    # epsimo projects
    projects_parser = subparsers.add_parser("projects", help="List projects")
    projects_parser.add_argument("--json", action="store_true", help="Output as JSON")
    projects_parser.set_defaults(func=cmd_projects)

    # epsimo credits {balance, buy}
    credits_parser = subparsers.add_parser("credits", help="Manage credits and thread usage")
    credits_subparsers = credits_parser.add_subparsers(dest="credits_command", help="Credits command")
    
    balance_parser = credits_subparsers.add_parser("balance", help="Check current credit balance")
    balance_parser.set_defaults(func=cmd_balance)
    
    buy_parser = credits_subparsers.add_parser("buy", help="Buy more credits")
    buy_parser.add_argument("--quantity", type=int, required=True, help="Number of threads to purchase")
    buy_parser.add_argument("--amount", type=float, help="Total amount to pay in EUR (optional, calculated if omitted)")
    buy_parser.set_defaults(func=cmd_buy)

    # epsimo assistants --project-id X
    assistants_parser = subparsers.add_parser("assistants", help="List assistants")
    assistants_parser.add_argument("--project-id", required=True, help="Project ID")
    assistants_parser.add_argument("--json", action="store_true", help="Output as JSON")
    assistants_parser.set_defaults(func=cmd_assistants)

    # epsimo threads --project-id X
    threads_parser = subparsers.add_parser("threads", help="List threads")
    threads_parser.add_argument("--project-id", required=True, help="Project ID")
    threads_parser.set_defaults(func=cmd_threads)

    # epsimo run --project-id X --assistant-id Y
    run_parser = subparsers.add_parser("run", help="Run a terminal chat session")
    run_parser.add_argument("--project-id", required=True, help="Project ID")
    run_parser.add_argument("--assistant-id", required=True, help="Assistant ID")
    run_parser.set_defaults(func=cmd_run)

    # epsimo db query --project-id X --thread-id Y
    db_parser = subparsers.add_parser("db", help="Manage Virtual Database state")
    db_subparsers = db_parser.add_subparsers(dest="db_command", help="DB command")
    
    query_parser = db_subparsers.add_parser("query", help="Query the current state of a thread")
    query_parser.add_argument("--project-id", required=True, help="Project ID")
    query_parser.add_argument("--thread-id", required=True, help="Thread ID")
    query_parser.set_defaults(func=cmd_db)

    set_parser = db_subparsers.add_parser("set", help="Set a value in the thread state")
    set_parser.add_argument("--project-id", required=True, help="Project ID")
    set_parser.add_argument("--thread-id", required=True, help="Thread ID")
    set_parser.add_argument("--key", required=True, help="Key to set")
    set_parser.add_argument("--value", required=True, help="Value to set (JSON strings supported)")
    set_parser.set_defaults(func=cmd_db_set)

    args = parser.parse_args()
    
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
