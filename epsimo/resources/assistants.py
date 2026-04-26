class Assistants:
    def __init__(self, client):
        self.client = client

    def list(self, project_id):
        """List assistants in a project."""
        headers = self.client.get_project_headers(project_id)
        return self.client.request("GET", "/assistants/", headers=headers)

    def _prepare_payload(self, name, model="gpt-4o", instructions="", tools=None, public=False):
        """Prepare assistant payload with platform-specific normalization."""
        import os
        
        final_tools = []
        if tools:
            for t in tools:
                if isinstance(t, str):
                    t_lower = t.lower()
                    if t_lower in ["retrieval", "retriever"]:
                        final_tools.append({
                            "id": f"retrieval-{os.urandom(4).hex()}",
                            "name": "Retrieval",
                            "type": "retrieval",
                            "description": "Look up information in uploaded files.",
                            "config": {}
                        })
                    elif t_lower in ["search_tavily", "tavily"]:
                        final_tools.append({
                            "id": f"search_tavily-{os.urandom(4).hex()}",
                            "name": "Search (Tavily)",
                            "type": "search_tavily",
                            "description": "Uses the Tavily search engine. Includes sources in the response.",
                            "config": {}
                        })
                    else:
                        final_tools.append({
                            "id": f"{t_lower}-{os.urandom(4).hex()}",
                            "name": t,
                            "type": t_lower,
                            "description": "",
                            "config": {}
                        })
                else:
                    if isinstance(t, dict):
                        t_lower = t.get("type", "").lower()
                        normalized_tool = {
                            "id": f"{t_lower}-{os.urandom(4).hex()}",
                            "name": t.get("name") or t.get("type", "Unknown Tool"),
                            "type": t_lower,
                            "description": t.get("description", ""),
                            "config": t.get("config", {})
                        }
                        
                        # Add defaults if missing for standard types
                        if t_lower in ["retrieval", "retriever"] and not normalized_tool["description"]:
                            normalized_tool["name"] = "Retrieval"
                            normalized_tool["description"] = "Look up information in uploaded files."
                        elif t_lower in ["search_tavily", "tavily"] and not normalized_tool["description"]:
                            normalized_tool["name"] = "Search (Tavily)"
                            normalized_tool["description"] = "Uses the Tavily search engine. Includes sources in the response."
                            
                        # Keep any extra keys the user might have provided (like max_results)
                        for k, v in t.items():
                             if k not in normalized_tool and k != "type":
                                  normalized_tool["config"][k] = v
                                  
                        final_tools.append(normalized_tool)
        configurable = {
            "type": "agent",
            "type==agent/agent_type": "agent",
            "type==agent/system_message": instructions,
            "type==agent/tools": final_tools
        }
        
        return {
            "name": name,
            "config": {
                "configurable": configurable
            },
            "metadata": {}, 
            "tags": [],
            "public": public
        }

    def create(self, project_id, name, model="gpt-4o", instructions="", tools=None, public=False):
        """Create a new assistant."""
        headers = self.client.get_project_headers(project_id)
        payload = self._prepare_payload(name, model, instructions, tools, public)
        return self.client.request("POST", "/assistants/", json=payload, headers=headers)

    def get(self, project_id, assistant_id):
        """Get assistant details."""
        headers = self.client.get_project_headers(project_id)
        return self.client.request("GET", f"/assistants/{assistant_id}", headers=headers)

    def update(self, project_id, assistant_id, payload):
        """Update assistant settings."""
        headers = self.client.get_project_headers(project_id)
        return self.client.request("PUT", f"/assistants/{assistant_id}", json=payload, headers=headers)

    def delete(self, project_id, assistant_id):
        """Delete an assistant."""
        headers = self.client.get_project_headers(project_id)
        return self.client.request("DELETE", f"/assistants/{assistant_id}", headers=headers)
