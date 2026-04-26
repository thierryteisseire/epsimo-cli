class Projects:
    def __init__(self, client):
        self.client = client

    def list(self):
        """List all projects."""
        return self.client.request("GET", "/projects/")

    def create(self, name, description="Epsimo Project"):
        """Create a new project."""
        payload = {
            "name": name, 
            "description": description,
            "metadata": {} # Ensure metadata is present for UI stability
        }
        return self.client.request("POST", "/projects/", json=payload)

    def get(self, project_id):
        """Get project details (and token context switching)."""
        return self.client.request("GET", f"/projects/{project_id}")

    def update(self, project_id, name=None, description=None, metadata=None):
        """Update a project."""
        payload = {}
        if name: payload["name"] = name
        if description: payload["description"] = description
        if metadata is not None:
             payload["metadata"] = metadata
        else:
             payload["metadata"] = {}
             
        return self.client.request("PUT", f"/projects/{project_id}", json=payload)

    def delete(self, project_id, confirm=False):
        """Delete a project."""
        url = f"/projects/{project_id}"
        if confirm:
            url += "?confirm=true"
        return self.client.request("DELETE", url)
