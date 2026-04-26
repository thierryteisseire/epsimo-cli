class Credits:
    def __init__(self, client):
        self.client = client

    def get_balance(self):
        """Retrieve the current thread and credit balance."""
        # Using the thread-info endpoint as it contains current balance data
        return self.client.request("GET", "/auth/thread-info")

    def create_checkout_session(self, quantity, total_amount):
        """Create a checkout session to buy credits."""
        payload = {
            "quantity": quantity,
            "total_amount": float(total_amount)
        }
        return self.client.request("POST", "/checkout/create-checkout-session", json=payload)
