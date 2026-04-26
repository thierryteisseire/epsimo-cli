
import os
import sys
import argparse
import requests
import json
from auth import get_token, get_project_token, API_BASE_URL

def list_files(project_id, assistant_id):
    token = get_token()
    
    # Get project specific token
    project_token = get_project_token(project_id)

    headers = {"Authorization": f"Bearer {project_token}"}
    response = requests.get(f"{API_BASE_URL}/assistants/{assistant_id}/files", headers=headers)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

def upload_file(project_id, assistant_id, file_path):
    token = get_token()
    
    # Get project specific token
    auth_headers = {"Authorization": f"Bearer {token}"}
    proj_resp = requests.get(f"{API_BASE_URL}/projects/{project_id}", headers=auth_headers)
    proj_resp.raise_for_status()
    data = proj_resp.json()
    project_token = data.get('access_token') or data.get('token') or data.get('jwt_token')
    
    headers = {"Authorization": f"Bearer {project_token}"}
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    with open(file_path, 'rb') as f:
        files = {'files': (os.path.basename(file_path), f)}
        response = requests.post(
            f"{API_BASE_URL}/assistants/{assistant_id}/files",
            headers=headers,
            files=files
        )
    
    if not response.ok:
        print(f"Error: {response.text}")
    
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

def main():
    parser = argparse.ArgumentParser(description="Manage EpsimoAI Assistant Files")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List
    list_parser = subparsers.add_parser("list", help="List files for an assistant")
    list_parser.add_argument("--project-id", required=True, help="Project ID")
    list_parser.add_argument("--assistant-id", required=True, help="Assistant ID")

    # Upload
    upload_parser = subparsers.add_parser("upload", help="Upload a file to an assistant")
    upload_parser.add_argument("--project-id", required=True, help="Project ID")
    upload_parser.add_argument("--assistant-id", required=True, help="Assistant ID")
    upload_parser.add_argument("--file", required=True, help="Path to file to upload")

    args = parser.parse_args()

    if args.command == "list":
        list_files(args.project_id, args.assistant_id)
    elif args.command == "upload":
        upload_file(args.project_id, args.assistant_id, args.file)

if __name__ == "__main__":
    main()
