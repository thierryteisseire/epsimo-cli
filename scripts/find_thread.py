
import requests
import json
from auth import get_token, API_BASE_URL

target_thread_id = "2b4c6325-c400-4e78-81c8-ef7781bf8b49"

def check_thread():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Checking thread {target_thread_id} with User Token...")
    try:
        resp = requests.get(f"{API_BASE_URL}/threads/{target_thread_id}", headers=headers)
        if resp.ok:
            t = resp.json()
            print(f"FOUND with User Token!")
            print(json.dumps(t, indent=2))
            return
        else:
            print(f"User Token check failed: {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Fallback: check projects
    resp = requests.get(f"{API_BASE_URL}/projects/", headers=headers)
    projects = resp.json()
    
    for p in projects:
        pid = p['project_id']
        pname = p['name']
        
        # Get project token
        pr = requests.get(f"{API_BASE_URL}/projects/{pid}", headers=headers)
        if not pr.ok:
            continue
        ptoken = pr.json().get('access_token')
        pheaders = {"Authorization": f"Bearer {ptoken}"}
        
        try:
            resp = requests.get(f"{API_BASE_URL}/threads/{target_thread_id}", headers=pheaders)
            if resp.ok:
                t = resp.json()
                print(f"FOUND in Project: {pname} ({pid})")
                print(json.dumps(t, indent=2))
                return
            else:
                 pass # Not in this project
        except:
            pass
            
    print("Thread not found by ID.")

if __name__ == "__main__":
    check_thread()
