
import os
import sys
import argparse
import requests
import json
from auth import get_token, get_project_token, API_BASE_URL

def stream_run(project_id, thread_id, message, assistant_id=None):
    token = get_token()
    
    # Get project specific token
    project_token = get_project_token(project_id)

    headers = {
        "Authorization": f"Bearer {project_token}",
        "Accept": "text/event-stream"
    }
    
    # Matches frontend structure in ThreadsPage.handleSendMessage
    payload = {
        "thread_id": thread_id,
        "input": [{
            "content": message,
            "type": "human",
            "role": "user"
        }],
        "stream_mode": ["messages", "events", "values"]
    }
    
    # Frontend doesn't pass assistant_id here, but we can if API supports override.
    # Frontend relies on thread <-> assistant link.
    if assistant_id:
        payload["assistant_id"] = assistant_id
    
    response = requests.post(f"{API_BASE_URL}/runs/stream", headers=headers, json=payload, stream=True)
    
    if not response.ok:
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")
    
    response.raise_for_status()
    
    print("Streaming response...")
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data:"):
                data_str = decoded_line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    print(json.dumps(data, indent=None))
                except json.JSONDecodeError:
                    print(f"Raw: {data_str}")

def main():
    parser = argparse.ArgumentParser(description="Manage EpsimoAI Runs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Stream
    stream_parser = subparsers.add_parser("stream", help="Stream a run")
    stream_parser.add_argument("--project-id", required=True, help="Project ID")
    stream_parser.add_argument("--thread-id", required=True, help="Thread ID")
    stream_parser.add_argument("--message", required=True, help="User message")
    stream_parser.add_argument("--assistant-id", help="Optional Assistant ID override (default: uses thread's assistant)")

    args = parser.parse_args()

    if args.command == "stream":
        stream_run(args.project_id, args.thread_id, args.message, args.assistant_id)

if __name__ == "__main__":
    main()
