import sys
import os
import json

# Add parent dir to path to find epsimo package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from epsimo import EpsimoClient
from epsimo.auth import get_token

def test_vdb():
    print("🧪 Testing Virtual Database via Threads...")
    
    # Needs a real project and thread from the user's environment
    PROJECT_ID = "cb323eb1-768e-4702-b7af-c73a1d6ce0e1"
    
    try:
        token = get_token()
        client = EpsimoClient(api_key=token)
        
        # 1. Create a fresh thread for DB testing
        print("Creating fresh DB thread...")
        # Get an assistant first
        assistants = client.assistants.list(PROJECT_ID)
        if not assistants:
            print("❌ No assistants found in project.")
            return
        
        asst_id = assistants[0]["assistant_id"]
        thread = client.threads.create(PROJECT_ID, "Virtual DB Test", asst_id)
        thread_id = thread["thread_id"]
        print(f"✅ Thread Created: {thread_id}")
        
        # 2. Set some structured data
        print("Setting data in DB...")
        db_data = {
            "user_settings": {
                "theme": "dark",
                "notifications": True
            },
            "last_login": "2026-02-03",
            "active_session": True
        }
        
        client.threads.set_state(PROJECT_ID, thread_id, db_data)
        print("✅ Data persisted.")
        
        # 3. Retrieve and verify
        print("Querying DB...")
        state = client.threads.get_state(PROJECT_ID, thread_id)
        values = state.get("values", {})
        
        print("\n=== Virtual DB Content ===")
        print(json.dumps(values, indent=2))
        
        if values.get("user_settings", {}).get("theme") == "dark":
            print("\n🎉 SUCCESS: Virtual Database is working correctly!")
        else:
            print("\n❌ FAILURE: Data mismatch or not found.")
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    test_vdb()
