
import sys
import json
import time
import requests
import uuid
from auth import get_token, get_project_token, API_BASE_URL

# --- Colors for Output ---
class Colors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    OKCYAN = '\033[96m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_pass(msg):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")

def print_fail(msg):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ️  {msg}{Colors.ENDC}")

def run_streaming_test():
    print(f"{Colors.HEADER}=== Starting Assistant Streaming Verification ==={Colors.ENDC}")

    # 1. Auth
    try:
        token = get_token()
        print_pass("Authenticated")
    except Exception as e:
        print_fail(f"Auth failed: {e}")
        return

    # 2. Project
    project_name = f"StreamTest {int(time.time())}"
    print_info(f"Creating project '{project_name}'...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.post(f"{API_BASE_URL}/projects/", headers=headers, json={"name": project_name, "description": "Streaming test"})
        resp.raise_for_status()
        project_id = resp.json()["project_id"]
        project_token = get_project_token(project_id)
        print_pass(f"Project created: {project_id}")
    except Exception as e:
        print_fail(f"Project creation failed: {e}")
        return

    # 3. Assistant
    print_info("Creating simple assistant...")
    p_headers = {"Authorization": f"Bearer {project_token}"}
    
    asst_payload = {
        "name": "Streaming Bot",
        "config": {
            "configurable": {
                "type": "agent",
                "type==agent/agent_type": "GPT-4O",
                "type==agent/model": "gpt-4o",
                "type==agent/system_message": "You are a helpful assistant. If asked to say something, say it exactly."
            }
        },
        "public": False
    }

    try:
        resp = requests.post(f"{API_BASE_URL}/assistants/", headers=p_headers, json=asst_payload)
        resp.raise_for_status()
        assistant_id = resp.json()["assistant_id"]
        print_pass(f"Assistant created: {assistant_id}")
    except Exception as e:
        print_fail(f"Assistant creation failed: {e}")
        return

    # 4. Thread
    print_info("Creating thread...")
    try:
        resp = requests.post(f"{API_BASE_URL}/threads/", headers=p_headers, json={"name": "Stream Thread", "assistant_id": assistant_id})
        resp.raise_for_status()
        thread_id = resp.json()["thread_id"]
        print_pass(f"Thread created: {thread_id}")
    except Exception as e:
        print_fail(f"Thread creation failed: {e}")
        return

    # 5. Streaming Run
    print_info("Ref: sending message 'Say: STREAMING_WORKS'...")
    
    stream_headers = {
        "Authorization": f"Bearer {project_token}",
        "Accept": "text/event-stream"
    }
    
    run_payload = {
        "thread_id": thread_id,
        "assistant_id": assistant_id,
        "input": [{"role": "user", "content": "Say: STREAMING_WORKS", "type": "human"}],
        "stream_mode": ["messages", "values"]
    }

    full_text = ""
    print(f"{Colors.OKCYAN}--- Stream Output Start ---{Colors.ENDC}")
    
    try:
        with requests.post(f"{API_BASE_URL}/runs/stream", headers=stream_headers, json=run_payload, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data:"):
                        data_str = decoded[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            # Attempt to parse json to find content (structure varies, so we print raw for debug if needed)
                            # Or just heuristic text accumulation
                             # Epsimo / LangGraph usually sends complex JSONs
                            data_json = json.loads(data_str)
                            
                            # Heuristic extraction for various formats
                            content = ""
                            if isinstance(data_json, list): # Often a list of ops
                                for item in data_json:
                                    if "content" in item:
                                        content = item["content"]
                            elif isinstance(data_json, dict):
                                if "messages" in data_json:
                                     # Extract last message content
                                     pass 
                                if "content" in data_json:
                                    content = data_json["content"]
                            
                            # Simple visual echo 
                            if content:
                                sys.stdout.write(content)
                                sys.stdout.flush()
                                full_text += content
                            else:
                                # Fallback if we can't parse structure easily, just check raw for test
                                pass
                        except:
                            pass
                            
        print(f"\n{Colors.OKCYAN}--- Stream Output End ---{Colors.ENDC}")
        
        if "STREAMING_WORKS" in full_text:
            print_pass("Verification Successful: Received expected output!")
        else:
            print_fail("Did not receive exact expected phrase, but stream finished.")
            print_info(f"Received total length: {len(full_text)}")

    except Exception as e:
        print_fail(f"Streaming failed: {e}")

    # 6. Cleanup
    try:
        requests.delete(f"{API_BASE_URL}/projects/{project_id}?confirm=true", headers=headers)
        print_pass("Cleanup: Project deleted")
    except:
        pass

if __name__ == "__main__":
    run_streaming_test()
