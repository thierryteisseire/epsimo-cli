class Database:
    """
    The Database resource allows using Epsimo threads as a virtual structured storage.
    It wraps thread state management into a familiar key-value or document-based interface.
    """
    def __init__(self, client):
        self.client = client

    def get_all(self, project_id, thread_id):
        """Retrieve all structured data stored in the thread state."""
        state = self.client.threads.get_state(project_id, thread_id)
        return state.get("values", {})

    def get(self, project_id, thread_id, key, default=None):
        """Retrieve a specific key from the thread state."""
        values = self.get_all(project_id, thread_id)
        if isinstance(values, dict):
            return values.get(key, default)
        return default

    def set(self, project_id, thread_id, key, value):
        """
        Store a value in the thread state. 
        Note: This currently attempts a manual state update which may be restricted 
        depending on assistant configuration.
        """
        return self.client.threads.set_state(project_id, thread_id, {key: value})

    def update(self, project_id, thread_id, data):
        """Bulk update the thread state with a dictionary of values."""
        return self.client.threads.set_state(project_id, thread_id, data)
