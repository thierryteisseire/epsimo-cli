import os
import requests
from .auth import get_token
from .resources.projects import Projects
from .resources.assistants import Assistants
from .resources.threads import Threads
from .resources.files import Files
from .resources.credits import Credits
from .resources.db import Database

class EpsimoClient:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or os.environ.get("EPSIMO_API_KEY") or get_token()
        self.base_url = base_url or os.environ.get("EPSIMO_API_URL", "https://api.epsimoagents.com")
        
        # In the future, we might support API Keys directly.
        # For now, we reuse the JWT token logic but wrapped cleanly.
        # If the user passes a token as api_key, we use it.
        self._session = requests.Session()
        if self.api_key:
            self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            
        self.projects = Projects(self)
        self.assistants = Assistants(self)
        self.threads = Threads(self)
        self.files = Files(self)
        self.credits = Credits(self)
        self.db = Database(self)

    def request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        response = self._session.request(method, url, **kwargs)
        if not response.ok:
            try:
                import json
                print(f"❌ API Error ({response.status_code}): {json.dumps(response.json(), indent=2)}")
            except:
                print(f"❌ API Error ({response.status_code}): {response.text}")
            response.raise_for_status()
        if response.status_code == 204:
            return None
        return response.json()

    def get_project_headers(self, project_id):
        """Fetch/Construct headers including project-specific token."""
        # Using the clean client.projects access
        resp = self.projects.get(project_id)
        token = resp.get("access_token") or resp.get("token") or resp.get("jwt_token")
        
        if not token:
             # Just a warning or error?
             print(f"Warning: No specific token found for project {project_id}")
             
        return {"Authorization": f"Bearer {token}"}
