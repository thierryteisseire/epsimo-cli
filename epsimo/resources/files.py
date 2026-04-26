import os

class Files:
    def __init__(self, client):
        self.client = client

    def list(self, project_id, assistant_id):
        """List files attached to an assistant."""
        headers = self.client.get_project_headers(project_id)
        return self.client.request("GET", f"/assistants/{assistant_id}/files", headers=headers)

    def upload(self, project_id, assistant_id, file_path):
        """Upload a file to an assistant."""
        headers = self.client.get_project_headers(project_id)
        # requests handles Content-Type for files
        # We need to act directly on the session or expose a clean method in client
        
        # client.request takes json/params but not files explicitly in my simple wrapper
        # Let's bypass wrapper slightly or extend it, but here we construct full URL
        # reusing client.base_url
        
        url = f"{self.client.base_url}/assistants/{assistant_id}/files"
        
        # We need to strip standard JSON content type if present
        # but headers only has Auth here.
        
        with open(file_path, 'rb') as f:
            files = {'files': (os.path.basename(file_path), f)}
            # accessing _session directly for file upload flexibility
            resp = self.client._session.post(url, headers=headers, files=files)
            
        if not resp.ok:
            resp.raise_for_status()
        return resp.json()

    def delete(self, project_id, assistant_id, file_id):
        """Delete a file from an assistant."""
        headers = self.client.get_project_headers(project_id)
        return self.client.request("DELETE", f"/assistants/{assistant_id}/files/{file_id}", headers=headers)
