
import os
import json
import time
import requests
import getpass
import sys
import subprocess
from pathlib import Path

# Configuration
API_BASE_URL = os.environ.get("EPSIMO_API_URL", "http://localhost:8000")
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

    # Return None instead of raising Error to let caller handle it (e.g. prompt login)
    return None

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

def login_interactive():
    """Interactive login flow."""
    use_modal = os.environ.get("USE_GUI_PROMPT") == "1"
    
    email = None
    if use_modal and sys.platform == 'darwin':
        email = get_input_via_applescript("Enter your Epsimo Email:")
    else:
        email = input("Email: ")

    if not email:
        print("Email is required.")
        return

    password = None
    if 'EPSIMO_PASSWORD' in os.environ:
        password = os.environ['EPSIMO_PASSWORD']
    elif use_modal and sys.platform == 'darwin':
        password = get_input_via_applescript("Enter your Epsimo Password:", hidden=True)
    else:
        password = getpass.getpass("Password: ")

    if not password:
         print("Password is required.")
         return

    try:
        perform_login(email, password, attempt_signup_on_fail=True)
    except Exception:
        pass

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
        token = data.get('access_token') or data.get('token') or data.get('jwt_token')
        
        if not token:
            raise ValueError("Failed to obtain access token from login response.")

        # Save token
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(data, f)
            
        print(f"✅ Successfully logged in as {email}")
        return token

    except requests.exceptions.HTTPError as e:
        print(f"❌ Login failed: {e}")
        if attempt_signup_on_fail:
             print("\nUser might not exist or password is wrong.")
             choice = input("Do you want to create a new account with these credentials? (y/n): ")
             if choice.lower() == 'y':
                 return perform_signup(email, password)
        raise
