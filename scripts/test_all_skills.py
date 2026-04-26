
import os
import sys
import json
import time
import requests
import uuid
from auth import get_token, get_project_token, API_BASE_URL

# --- Colors for Output ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_pass(msg):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")

def print_fail(msg):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ️  {msg}{Colors.ENDC}")

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {msg} ==={Colors.ENDC}")

class SkillTester:
    def __init__(self):
        self.access_token = None
        self.project_id = None
        self.project_token = None
        self.assistant_id = None
        self.thread_id = None
        self.file_path = "test_secret.txt"
        self.secret_code = f"TEST-SECRET-{uuid.uuid4().hex[:8]}"

    def step_1_auth(self):
        print_header("Step 1: Authentication")
        try:
            self.access_token = get_token()
            if not self.access_token:
                raise ValueError("No token returned")
            print_pass("Authentication successful")
            
            # Check Balance (Credits)
            headers = {"Authorization": f"Bearer {self.access_token}"}
            resp = requests.get(f"{API_BASE_URL}/auth/thread-info", headers=headers)
            if resp.ok:
                data = resp.json()
                print_info(f"Threads Used: {data.get('thread_counter')}/{data.get('thread_max')}")
            else:
                print_fail("Could not fetch balance")

        except Exception as e:
            print_fail(f"Auth failed: {e}")
            sys.exit(1)

    def step_2_projects(self):
        print_header("Step 2: Project Management")
        
        # Create
        unique_name = f"AutoTest Project {int(time.time())}"
        print_info(f"Creating project: {unique_name}")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "name": unique_name,
            "description": "Automated test project"
        }
        
        try:
            resp = requests.post(f"{API_BASE_URL}/projects/", headers=headers, json=payload)
            if not resp.ok:
                raise ValueError(f"Project creation failed: {resp.text}")
            
            data = resp.json()
            self.project_id = data["project_id"]
            print_pass(f"Created project {self.project_id}")
            
            # Get Project Token
            self.project_token = get_project_token(self.project_id)
            print_pass("Retrieved project-specific token")

        except Exception as e:
            print_fail(f"Project step failed: {e}")
            sys.exit(1)

    def step_3_assistants(self):
        print_header("Step 3: Assistant Management")
        
        headers = {"Authorization": f"Bearer {self.project_token}"}
        
        # Create
        name = f"AutoTest Assistant {uuid.uuid4().hex[:4]}"
        
        # Configuration matches updated assistant.py logic
        instructions = "You are a test assistant. You HAVE access to uploaded files. Use the Retrieval tool to find the secret code."
        
        configurable = {
            "type": "agent",
            "type==agent/agent_type": "GPT-4O", 
            "type==agent/llm_type": "gpt-4o",
            "type==agent/model": "gpt-4o",
            "type==agent/system_message": instructions,
            "type==agent/tools": [
                {
                    "id": f"retrieval-{uuid.uuid4().hex[:4]}", 
                    "name": "Retrieval", 
                    "type": "retrieval",
                     "description": "Look up information in uploaded files.",
                    "config": {}
                },
                {
                     "id": f"ddg-{uuid.uuid4().hex[:4]}",
                     "name": "DuckDuckGo Search",
                     "type": "ddg_search",
                     "description": "Search web",
                     "config": {}
                }
            ]
        }
        
        payload = {
            "name": name,
            "config": {
                "configurable": configurable
            },
            "public": True
        }
        
        try:
            print_info(f"Creating assistant: {name}")
            resp = requests.post(f"{API_BASE_URL}/assistants/", headers=headers, json=payload)
            if not resp.ok:
                raise ValueError(f"Create assistant failed: {resp.text}")
            
            data = resp.json()
            self.assistant_id = data["assistant_id"]
            print_pass(f"Created assistant {self.assistant_id}")
            
            # List to verify
            resp_list = requests.get(f"{API_BASE_URL}/assistants/", headers=headers)
            if not resp_list.ok:
                raise ValueError("List assistants failed")
            
            assistants = resp_list.json()
            found = any(a["assistant_id"] == self.assistant_id for a in assistants)
            if found:
                print_pass("Verification: Assistant found in list")
            else:
                print_fail("Verification: Assistant NOT found in list")

        except Exception as e:
            print_fail(f"Assistant step failed: {e}")
            # Don't exit, might be able to cleanup other things

    def step_4_files(self):
        print_header("Step 4: File Management")
        if not self.assistant_id:
            print_fail("Skipping files (no assistant)")
            return

        # Create dummy file
        with open(self.file_path, "w") as f:
            f.write(f"CONFIDENTIAL DATA\nThe secret code is: {self.secret_code}")
        
        headers = {"Authorization": f"Bearer {self.project_token}"}
        
        try:
            print_info(f"Uploading file with secret: {self.secret_code}")
            with open(self.file_path, 'rb') as f:
                files = {'files': (os.path.basename(self.file_path), f)}
                resp = requests.post(f"{API_BASE_URL}/assistants/{self.assistant_id}/files", headers=headers, files=files)
            
            if not resp.ok:
                raise ValueError(f"Upload failed: {resp.text}")
            
            print_pass("File uploaded successfully")
            
            # List files
            resp_list = requests.get(f"{API_BASE_URL}/assistants/{self.assistant_id}/files", headers=headers)
            if resp_list.ok:
                files_list = resp_list.json()
                if len(files_list) > 0:
                    print_pass(f"Verified {len(files_list)} file(s) attached")
                else:
                    print_fail("File list empty")

        except Exception as e:
            print_fail(f"File step failed: {e}")
        finally:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)

    def step_5_threads(self):
        print_header("Step 5: Thread Management")
        if not self.project_token:
             print_fail("Skipping threads (no project token)")
             return

        headers = {"Authorization": f"Bearer {self.project_token}"}
        name = f"Test Thread {uuid.uuid4().hex[:4]}"
        
        payload = {
            "name": name,
            "metadata": {"type": "thread"},
            "assistant_id": self.assistant_id
        }
        
        try:
            print_info(f"Creating thread: {name}")
            resp = requests.post(f"{API_BASE_URL}/threads/", headers=headers, json=payload)
            if not resp.ok:
                 raise ValueError(f"Create thread failed: {resp.text}")
            
            data = resp.json()
            self.thread_id = data["thread_id"]
            print_pass(f"Created thread {self.thread_id}")

        except Exception as e:
            print_fail(f"Thread step failed: {e}")
            sys.exit(1)

    def step_6_execution(self):
        print_header("Step 6: Execution (Runs & RAG)")
        if not self.thread_id or not self.assistant_id:
            print_fail("Skipping execution (missing resources)")
            return

        headers = {
            "Authorization": f"Bearer {self.project_token}",
            "Accept": "text/event-stream"
        }
        
        payload = {
            "thread_id": self.thread_id,
            "assistant_id": self.assistant_id,
            "input": [{
                "content": "What is the secret code in the file?",
                "type": "human",
                "role": "user"
            }],
            "stream_mode": ["messages", "values"]
        }
        
        print_info("Streaming run request...")
        found_secret = False
        full_response = ""
        
        try:
            resp = requests.post(f"{API_BASE_URL}/runs/stream", headers=headers, json=payload, stream=True)
            if not resp.ok:
                 raise ValueError(f"Stream failed: {resp.status_code} {resp.text}")

            for line in resp.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data:"):
                        data_str = decoded[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            # Try to extract content delta or message
                            # This is a simplified check, actual structure varies
                            if self.secret_code in data_str:
                                found_secret = True
                            full_response += data_str
                        except:
                            pass
                            
            if found_secret:
                print_pass(f"RAG Successful! Secret '{self.secret_code}' found in stream.")
            else:
                # Polling retry logic for latency
                max_retries = 6
                for i in range(max_retries):
                    wait_time = 10
                    print_info(f"Secret not found. Retrying in {wait_time}s ({i+1}/{max_retries})...")
                    time.sleep(wait_time)
                    
                    full_response = ""
                    current_run_found = False
                    
                    try:
                        resp = requests.post(f"{API_BASE_URL}/runs/stream", headers=headers, json=payload, stream=True)
                        for line in resp.iter_lines():
                            if line:
                                decoded = line.decode('utf-8')
                                if decoded.startswith("data:"):
                                    data_str = decoded[5:].strip()
                                    if data_str == "[DONE]":
                                        break
                                    try:
                                        if self.secret_code in data_str:
                                            current_run_found = True
                                        full_response += data_str
                                    except:
                                        pass
                    except Exception as e:
                        print_fail(f"Retry {i+1} failed with error: {e}")
                        continue
                        
                    if current_run_found:
                        found_secret = True
                        print_pass(f"RAG Successful (on retry {i+1})! Secret '{self.secret_code}' found.")
                        break
                
                if not found_secret:
                    print_fail("Secret not found after retries.")
                    print_info(f"Last response dump (truncated): {full_response[:200]}...")

        except Exception as e:
            print_fail(f"Execution step failed: {e}")

    def step_7_credits_check(self):
        print_header("Step 7: Credits Purchase (Dry Run)")
        # Just verify we can generate a checkout link
        if not self.access_token: 
            return

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {"quantity": 100, "total_amount": 10.0}
        
        try:
            resp = requests.post(f"{API_BASE_URL}/checkout/create-checkout-session", json=payload, headers=headers)
            if resp.ok:
                url = resp.json().get("url")
                if url:
                    print_pass("Checkout session URL generated successfully")
                else:
                    print_fail("No URL in checkout response")
            else:
                print_fail(f"Checkout creation failed: {resp.text}")
        except Exception as e:
             print_fail(f"Credits step failed: {e}")

    def step_8_cleanup(self):
        print_header("Step 8: Cleanup")
        # cleanup is important
        
        headers = {"Authorization": f"Bearer {self.access_token}"} # Use main token for project deletion context switching
        
        if self.project_id:
            # We need to delete the project. 
            # Note: Deleting project *should* delete assistants/threads/files inside it.
            try:
                # Switch context explicitly just in case or use main token? api.d.ts says delete project uses /projects/{id}
                # And usually requires just access to it.
                
                # Check api.d.ts: delete_project_projects__project_id__delete
                # If confirm=true is needed
                print_info(f"Deleting project {self.project_id}...")
                resp = requests.delete(f"{API_BASE_URL}/projects/{self.project_id}?confirm=true", headers=headers)
                
                if resp.ok:
                    print_pass("Project deleted successfully")
                else:
                    print_fail(f"Project deletion failed: {resp.status_code} {resp.text}")
                    
            except Exception as e:
                print_fail(f"Cleanup failed: {e}")

    def run(self):
        print_header("🚀 STARTING COMPREHENSIVE EPSIMO SKILL TEST 🚀")
        self.step_1_auth()
        self.step_2_projects()
        self.step_3_assistants()
        self.step_4_files()
        self.step_5_threads()
        self.step_6_execution()
        self.step_7_credits_check()
        self.step_8_cleanup()
        print_header("🏁 TEST SUITE COMPLETE 🏁")

if __name__ == "__main__":
    tester = SkillTester()
    tester.run()
