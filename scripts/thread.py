
import os
import sys
import argparse
import requests
import json
from auth import get_token, get_project_token, API_BASE_URL

def create_thread(project_id, name, assistant_id=None):
    token = get_token()
    
    # Get project specific token
    project_token = get_project_token(project_id)

    headers = {"Authorization": f"Bearer {project_token}"}
    
    # Metadata structure from frontend
    payload = {
        "name": name,
        "metadata": {
            "configurable": {},
            "type": "thread"
        },
        "configurable": {
             "type": "agent"
        }
    }
    if assistant_id:
        payload["assistant_id"] = assistant_id
        
    response = requests.post(f"{API_BASE_URL}/threads/", headers=headers, json=payload)
    
    if not response.ok:
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")
        
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

def list_threads(project_id):
    token = get_token()
    
    # Get project specific token
    auth_headers = {"Authorization": f"Bearer {token}"}
    proj_resp = requests.get(f"{API_BASE_URL}/projects/{project_id}", headers=auth_headers)
    proj_resp.raise_for_status()
    data = proj_resp.json()
    project_token = data.get('access_token') or data.get('token') or data.get('jwt_token')

    headers = {"Authorization": f"Bearer {project_token}"}
    response = requests.get(f"{API_BASE_URL}/threads/", headers=headers)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

def main():
    parser = argparse.ArgumentParser(description="Manage EpsimoAI Threads")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List
    list_parser = subparsers.add_parser("list", help="List threads in a project")
    list_parser.add_argument("--project-id", required=True, help="Project ID")

    # Create
    create_parser = subparsers.add_parser("create", help="Create a new thread")
    create_parser.add_argument("--project-id", required=True, help="Project ID")
    create_parser.add_argument("--name", default="New Thread", help="Thread name")
    create_parser.add_argument("--assistant-id", help="Assistant ID to associate with the thread (optional)")

    args = parser.parse_args()

    if args.command == "list":
        list_threads(args.project_id)
    elif args.command == "create":
        create_thread(args.project_id, args.name, args.assistant_id)

if __name__ == "__main__":
    main()
