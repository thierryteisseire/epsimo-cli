
import os
import sys
import argparse
import requests
import json
from auth import get_token, API_BASE_URL

def list_projects():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/projects/", headers=headers)
    response.raise_for_status()
    projects = response.json()
    print(json.dumps(projects, indent=2))

def create_project(name, description):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"name": name, "description": description}
    response = requests.post(f"{API_BASE_URL}/projects/", headers=headers, json=payload)
    if not response.ok:
        print(f"Error {response.status_code}: {response.text}")
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

def get_project(project_id):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/projects/{project_id}", headers=headers)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

def main():
    parser = argparse.ArgumentParser(description="Manage EpsimoAI Projects")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List
    subparsers.add_parser("list", help="List all projects")

    # Get
    get_parser = subparsers.add_parser("get", help="Get project details")
    get_parser.add_argument("--id", required=True, help="Project ID")

    # Create
    create_parser = subparsers.add_parser("create", help="Create a new project")
    create_parser.add_argument("--name", required=True, help="Project name")
    create_parser.add_argument("--description", help="Project description", default="My AI Project")

    args = parser.parse_args()

    if args.command == "list":
        list_projects()
    elif args.command == "get":
        get_project(args.id)
    elif args.command == "create":
        create_project(args.name, args.description)

if __name__ == "__main__":
    main()
