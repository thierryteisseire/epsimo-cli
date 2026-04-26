
import os
import sys
import argparse
import requests
import json
from auth import get_token, get_project_token, API_BASE_URL

def create_assistant(project_id, name, instructions, model, tools=None):
    token = get_token()
    
    # Get project specific token
    project_token = get_project_token(project_id)
    
    headers = {"Authorization": f"Bearer {project_token}"}
    
    # Construct tools list similar to frontend
    final_tools = []
    if tools:
        for t_name in tools:
            t_lower = t_name.lower()
            if t_lower == "retrieval" or t_lower == "retriever":
                final_tools.append({
                    "id": f"retrieval-{os.urandom(4).hex()}",
                    "name": "Retrieval",
                    "type": "retrieval",
                    "description": "Look up information in uploaded files.",
                    "config": {}
                })
            elif "duckduckgo" in t_lower or "ddg" in t_lower:
                final_tools.append({
                    "id": f"ddg_search-{os.urandom(4).hex()}",
                    "name": "DuckDuckGo Search",
                    "type": "ddg_search",
                    "description": "Uses the DuckDuckGo search engine to find information on the web.",
                    "config": {}
                })
            elif "tavily" in t_lower:
                final_tools.append({
                    "id": f"search_tavily-{os.urandom(4).hex()}",
                    "name": "Search (Tavily)",
                    "type": "search_tavily",
                    "description": "Uses the Tavily search engine. Includes sources in the response.",
                    "config": {}
                })
            else:
                 # Generic fallback
                 final_tools.append({
                    "id": f"{t_name}-{os.urandom(4).hex()}",
                    "name": t_name,
                    "type": t_name,
                    "description": "",
                    "config": {}
                })

    # New config structure based on AssistantModal.tsx
    configurable = {
        "type": "agent",
        "type==agent/agent_type": model.upper(), 
        "type==agent/llm_type": model,
        "type==agent/model": model,
        "type==agent/system_message": instructions,
        "type==agent/tools": final_tools
    }
    
    payload = {
        "name": name,
        "config": {
            "configurable": configurable
        },
        "public": True 
    }
    
    response = requests.post(f"{API_BASE_URL}/assistants/", headers=headers, json=payload)
    if not response.ok:
        print(f"Error: {response.text}")
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

def list_assistants(project_id):
    token = get_token()
    
    # Get project specific token
    auth_headers = {"Authorization": f"Bearer {token}"}
    proj_resp = requests.get(f"{API_BASE_URL}/projects/{project_id}", headers=auth_headers)
    proj_resp.raise_for_status()
    data = proj_resp.json()
    project_token = data.get('access_token') or data.get('token') or data.get('jwt_token')

    headers = {"Authorization": f"Bearer {project_token}"}
    response = requests.get(f"{API_BASE_URL}/assistants/", headers=headers)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

def update_assistant(project_id, assistant_id, name=None, instructions=None, model=None, tools=None):
    token = get_token()
    
    # Get project specific token
    auth_headers = {"Authorization": f"Bearer {token}"}
    proj_resp = requests.get(f"{API_BASE_URL}/projects/{project_id}", headers=auth_headers)
    proj_resp.raise_for_status()
    data = proj_resp.json()
    project_token = data.get('access_token') or data.get('token') or data.get('jwt_token')
    
    headers = {"Authorization": f"Bearer {project_token}"}
    
    # Fetch existing assistant data first to merge
    existing_resp = requests.get(f"{API_BASE_URL}/assistants/{assistant_id}", headers=headers)
    existing_resp.raise_for_status()
    existing_data = existing_resp.json()
    
    config = existing_data.get("config", {})
    if instructions:
        config["system_prompt"] = instructions
    if model:
        config["model"] = model
    if tools is not None:
        config["tools"] = tools

    payload = {
        "name": name if name else existing_data.get("name"),
        "config": config,
        "public": existing_data.get("public", True)
    }
    
    response = requests.put(f"{API_BASE_URL}/assistants/{assistant_id}", headers=headers, json=payload)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))

def main():
    parser = argparse.ArgumentParser(description="Manage EpsimoAI Assistants")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List
    list_parser = subparsers.add_parser("list", help="List assistants in a project")
    list_parser.add_argument("--project-id", required=True, help="Project ID")

    # Create
    create_parser = subparsers.add_parser("create", help="Create a new assistant")
    create_parser.add_argument("--project-id", required=True, help="Project ID")
    create_parser.add_argument("--name", required=True, help="Assistant name")
    create_parser.add_argument("--instructions", required=True, help="System instructions")
    create_parser.add_argument("--model", default="gpt-4o", help="Model name (default: gpt-4o)")
    create_parser.add_argument("--tools", nargs="*", help="List of tools to enable (e.g. Retrieval DuckDuckGo)")

    # Update
    update_parser = subparsers.add_parser("update", help="Update an existing assistant")
    update_parser.add_argument("--project-id", required=True, help="Project ID")
    update_parser.add_argument("--assistant-id", required=True, help="Assistant ID")
    update_parser.add_argument("--name", help="New assistant name")
    update_parser.add_argument("--instructions", help="New system instructions")
    update_parser.add_argument("--model", help="New model name")
    update_parser.add_argument("--tools", nargs="*", help="New list of tools")

    args = parser.parse_args()

    if args.command == "list":
        list_assistants(args.project_id)
    elif args.command == "create":
        create_assistant(args.project_id, args.name, args.instructions, args.model, tools=args.tools)
    elif args.command == "update":
        update_assistant(args.project_id, args.assistant_id, args.name, args.instructions, args.model, tools=args.tools)

if __name__ == "__main__":
    main()
