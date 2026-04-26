
import os
import json
import time
import requests
import argparse
import getpass
import sys
import subprocess
from pathlib import Path

# Configuration
API_BASE_URL = os.environ.get("EPSIMO_API_URL", "https://api.epsimoagents.com")
TOKEN_FILE = Path.home() / ".epsimo_token"

def get_token():
    """Retrieve a valid JWT token, refreshing if necessary."""
    
    # Check if token file exists
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                return data.get('access_token') or data.get('token') or data.get('jwt_token')
        except json.JSONDecodeError:
            pass
            
    # Try logging in with env vars if file doesn't exist/is invalid
    if os.environ.get("EPSIMO_EMAIL") and os.environ.get("EPSIMO_PASSWORD"):
        return perform_login(os.environ.get("EPSIMO_EMAIL"), os.environ.get("EPSIMO_PASSWORD"))

    raise RuntimeError("Authentication required. Please run `python3 .agent/skills/epsimo-agent/scripts/auth.py login` or set EPSIMO_EMAIL and EPSIMO_PASSWORD environment variables.")

def get_project_token(project_id):
    """Get a project-specific token."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/projects/{project_id}", headers=headers)
    response.raise_for_status()
    data = response.json()
    project_token = data.get('access_token') or data.get('token') or data.get('jwt_token')
    if not project_token:
        raise ValueError(f"Failed to obtain project token for project {project_id}")
    return project_token

def perform_signup(email, password):
    """Register a new user."""
    print(f"Attempting to register new user: {email}")
    url = f"{API_BASE_URL}/auth/signup"
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Signup successful! Logging in...")
        return perform_login(email, password)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400: # Usually "User already exists" or validation error
             print(f"⚠️ Signup failed: {e.response.text}")
        else:
             print(f"❌ Signup failed: {e}")
        raise

def get_input_via_applescript(prompt, hidden=False):
    """Get input using macOS native dialog."""
    try:
        script = f'display dialog "{prompt}" default answer ""'
        if hidden:
            script += ' with hidden answer'
        script += ' buttons {"Cancel", "OK"} default button "OK"'
        
        cmd = ['osascript', '-e', script]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Parse result: button returned:OK, text returned:foobar
        output = result.stdout.strip()
        if "text returned:" in output:
            return output.split("text returned:")[-1]
        return ""
    except subprocess.CalledProcessError:
        return None

def perform_login(email, password, attempt_signup_on_fail=False):
    """Login logic."""
    if not email or not password:
        raise ValueError("Email and password are required.")

    url = f"{API_BASE_URL}/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # DEBUG: Print keys if structure is unexpected
        token = data.get('access_token')
        
        if not token:
             token = data.get('token')
             
        if not token:
             token = data.get('jwt_token')
             
        if not token:
            print(f"⚠️ Debug: Full response data keys: {list(data.keys())}")
            print(f"⚠️ Debug: Full response data: {data}")
            raise ValueError("Failed to obtain access token from login response.")

        # Save token
        with open(TOKEN_FILE, 'w') as f:
            json.dump(data, f)
            
        print(f"✅ Successfully logged in as {email}")
        return token

    except requests.exceptions.HTTPError as e:
        print(f"❌ Login failed: {e}")
        # If UNAUTHORIZED, it might mean user doesn't exist OR bad password.
        if attempt_signup_on_fail:
             print("\nUser might not exist or password is wrong.")
             
             # Check if we should use GUI for prompt
             if sys.platform == 'darwin' and os.environ.get("USE_GUI_PROMPT"):
                 # Simple popup confirming desire to signup? Hard to do strictly y/n
                 # Just use CLI for choices for simplicity, or assume yes if they explicitly ran setup
                 pass
                 
             choice = input("Do you want to create a new account with these credentials? (y/n): ")
             if choice.lower() == 'y':
                 return perform_signup(email, password)
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EpsimoAI Authentication")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Authenticate with EpsimoAI")
    login_parser.add_argument("--email", help="Your email address")
    login_parser.add_argument("--password", help="Your password (optional, will prompt if missing)")
    login_parser.add_argument("--modal", action="store_true", help="Use macOS modal dialogs for input")

    args = parser.parse_args()

    if args.command == "login":
        email = args.email
        password = args.password
        use_modal = args.modal or os.environ.get("USE_GUI_PROMPT") == "1"

        if not email:
            if use_modal and sys.platform == 'darwin':
                email = get_input_via_applescript("Enter your Epsimo Email:")
            else:
                email = input("Email: ")
        
        if not email:
            print("Email is required.")
            sys.exit(1)

        if not password:
            if 'EPSIMO_PASSWORD' in os.environ:
                password = os.environ['EPSIMO_PASSWORD']
            elif use_modal and sys.platform == 'darwin':
                password = get_input_via_applescript("Enter your Epsimo Password:", hidden=True)
            else:
                password = getpass.getpass("Password: ")
        
        if not password:
             print("Password is required.")
             sys.exit(1)

        try:
            # We enable auto-signup prompt for interactive login
            # Pass choice to use GUI prompts if needed
            if use_modal:
                os.environ["USE_GUI_PROMPT"] = "1"
            perform_login(email, password, attempt_signup_on_fail=True)
        except Exception:
            sys.exit(1)
            
    else:
        # Default behavior: test token retrieval
        try:
            token = get_token()
            print(f"Token: {token[:10]}...") 
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
