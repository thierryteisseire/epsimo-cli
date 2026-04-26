import json

class Threads:
    def __init__(self, client):
        self.client = client

    def list(self, project_id):
        """List threads in a project."""
        headers = self.client.get_project_headers(project_id)
        return self.client.request("GET", "/threads/", headers=headers)

    def create(self, project_id, name, assistant_id, metadata=None):
        """Create a new thread."""
        headers = self.client.get_project_headers(project_id)
        payload = {
            "name": name,
            "assistant_id": assistant_id,
            "metadata": metadata or {"type": "thread"}
        }
        return self.client.request("POST", "/threads/", json=payload, headers=headers)

    def get(self, project_id, thread_id):
        """Get thread details."""
        headers = self.client.get_project_headers(project_id)
        return self.client.request("GET", f"/threads/{thread_id}", headers=headers)

    def get_state(self, project_id, thread_id):
        """Retrieve the structured state (values) of a thread."""
        headers = self.client.get_project_headers(project_id)
        return self.client.request("GET", f"/threads/{thread_id}/state", headers=headers)

    def set_state(self, project_id, thread_id, values, config=None):
        """Update the structured state (values) of a thread."""
        headers = self.client.get_project_headers(project_id)
        payload = {
            "values": values,
            "config": config or {}
        }
        return self.client.request("POST", f"/threads/{thread_id}/state", json=payload, headers=headers)

    def delete(self, project_id, thread_id):
        """Delete a thread."""
        headers = self.client.get_project_headers(project_id)
        return self.client.request("DELETE", f"/threads/{thread_id}", headers=headers)

    # --- Runs (Streaming) ---
    # Putting this here for convenience as Runs are usually per-thread/assistant
    
    def run_stream(self, project_id, thread_id, assistant_id, message, stream_mode=None):
        """
        Stream a run and yield chunks.
        
        Args:
            project_id: Project ID
            thread_id: Thread ID
            assistant_id: Assistant ID
            message: User message input string
            stream_mode: List of modes, e.g. ["messages", "values"]
            
        Yields:
            Parsed JSON chunks from the SSE stream.
        """
        headers = self.client.get_project_headers(project_id)
        headers["Accept"] = "text/event-stream"
        
        payload = {
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "input": [{"role": "user", "content": message, "type": "human"}],
            "stream_mode": stream_mode or ["messages", "values"]
        }
        
        # Bypass client.request to handle streaming
        url = f"{self.client.base_url}/runs/stream"
        response = self.client._session.post(url, json=payload, headers=headers, stream=True)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data:"):
                    data_str = decoded[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        yield json.loads(data_str)
                    except json.JSONDecodeError:
                        yield {"raw": data_str, "error": "json_decode_error"}
