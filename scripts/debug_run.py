
import requests
import os
import json
from auth import get_token, API_BASE_URL

projectId = "5d4025a5-5db7-4b6c-99b0-5b65e97d88c0"
assistantId = "a4178aa5-63d3-468b-8672-c6d916153d0a"
threadId = "2b4c6325-c400-4e78-81c8-ef7781bf8b49"
message = "Research Google"

def debug_run():
    token = get_token()
    auth_headers = {"Authorization": f"Bearer {token}"}
    proj_resp = requests.get(f"{API_BASE_URL}/projects/{projectId}", headers=auth_headers)
    data = proj_resp.json()
    project_token = data.get('access_token')

    headers = {
        "Authorization": f"Bearer {project_token}",
        "Accept": "text/event-stream"
    }

    payload = {
        "assistant_id": assistantId,
        "thread_id": threadId,
        "input": [{"type": "human", "content": message}]
    }

    print(f"Testing url: {API_BASE_URL}/runs/stream")
    r1 = requests.post(f"{API_BASE_URL}/runs/stream", headers=headers, json=payload, allow_redirects=False)
    print(f"No Slash: {r1.status_code}")
    print(r1.headers)

    print(f"Testing url: {API_BASE_URL}/runs/stream/")
    r2 = requests.post(f"{API_BASE_URL}/runs/stream/", headers=headers, json=payload, allow_redirects=False)
    print(f"With Slash: {r2.status_code}")
    print(r2.headers)

if __name__ == "__main__":
    debug_run()
