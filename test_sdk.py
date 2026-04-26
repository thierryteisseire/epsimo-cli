
import sys
import os
import time
# Add the current directory to sys.path so we can import 'epsimo' and 'scripts'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from epsimo import EpsimoClient
# Reuse auth helper to get a token for testing
from scripts.auth import get_token

def test_sdk():
    print("🚀 Testing Epsimo Python SDK...")
    
    # Authenticate
    token = get_token()
    client = EpsimoClient(api_key=token)
    print("✅ Client initialized")

    # 1. Create Project
    p_name = f"SDK Test {int(time.time())}"
    print(f"Creating project '{p_name}'...")
    project = client.projects.create(name=p_name, description="SDK Test Project")
    p_id = project["project_id"]
    print(f"✅ Project Created: {p_id}")

    # 2. Create Assistant
    print("Creating assistant...")
    asst = client.assistants.create(
        project_id=p_id, 
        name="SDK Bot", 
        instructions="You are a bot created via the SDK.",
        model="gpt-4o"
    )
    a_id = asst["assistant_id"]
    print(f"✅ Assistant Created: {a_id}")

    # 3. Create Thread
    print("Creating thread...")
    thread = client.threads.create(project_id=p_id, name="SDK Thread", assistant_id=a_id)
    t_id = thread["thread_id"]
    print(f"✅ Thread Created: {t_id}")

    # 4. Stream Run
    print("Streaming run...")
    print("--- Output ---")
    stream = client.threads.run_stream(
        project_id=p_id,
        thread_id=t_id,
        assistant_id=a_id,
        message="Say 'Hello from SDK'"
    )
    
    full_text = ""
    for chunk in stream:
        # print(f"DEBUG CHUNK: {chunk}")
        content_found = None
        
        if isinstance(chunk, list):
            for item in chunk:
                if isinstance(item, dict) and "content" in item:
                    content_found = item["content"]
                    break # Usually one message per chunk update in this mode
        elif isinstance(chunk, dict) and "content" in chunk:
            content_found = chunk["content"]
            
        if content_found:
            sys.stdout.write(content_found)
            full_text += content_found
            
    print("\n--- End Output ---")
    if "Hello from SDK" in full_text:
        print("✅ Streaming Success")
    else:
        print("⚠️ Streaming finished but expected text not found.")

    # 5. Cleanup
    print("Cleaning up...")
    client.projects.delete(p_id, confirm=True)
    print("✅ Project Deleted")

if __name__ == "__main__":
    test_sdk()
