#!/usr/bin/env python3
import sys
import os
import argparse
import json
import requests
from auth import get_token, login

BASE_URL = os.environ.get("EPSIMO_API_URL", "https://api.epsimoagents.com")

def check_balance():
    """Check the current thread and credit balance."""
    token = get_token()
    if not token:
        print("Not authenticated. Please login first.")
        return

    try:
        # Try retrieving full thread info
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/thread-info", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            thread_count = data.get("thread_counter", 0)
            thread_max = data.get("thread_max", 0)
            remaining = thread_max - thread_count
            
            print("\n=== Thread Balance ===")
            print(f"Threads Used:      {thread_count}")
            print(f"Total Allowance:   {thread_max}")
            print(f"Threads Remaining: {remaining}")
            print("======================\n")
        else:
            print(f"Error checking balance: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def buy_credits(quantity, total_amount=None):
    """Create a checkout session to buy credits."""
    token = get_token()
    if not token:
        print("Not authenticated. Please login first.")
        return

    # Simple logic for price estimation if not provided
    # Assuming roughly €0.10 per thread for small amounts, cheaper for bulk
    if total_amount is None:
        if quantity >= 1000:
            price_per_unit = 0.08
        elif quantity >= 500:
            price_per_unit = 0.09
        else:
            price_per_unit = 0.10
        
        total_amount = round(quantity * price_per_unit, 2)
        print(f"Estimated cost: {total_amount} EUR")

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "quantity": quantity,
            "total_amount": float(total_amount)
        }
        
        print("Creating checkout session...")
        response = requests.post(f"{BASE_URL}/checkout/create-checkout-session", json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            checkout_url = data.get("url")
            print("\nCheckout session created successfully!")
            print(f"Please visit this URL to complete your purchase:\n\n{checkout_url}\n")
        else:
            print(f"Error creating checkout session: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Manage credits and thread usage")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Balance command
    subparsers.add_parser("balance", help="Check current credit balance")
    
    # Buy command
    buy_parser = subparsers.add_parser("buy", help="Buy more credits")
    buy_parser.add_argument("--quantity", type=int, required=True, help="Number of threads to purchase")
    buy_parser.add_argument("--amount", type=float, help="Total amount to pay in EUR (optional, calculated if omitted)")

    args = parser.parse_args()
    
    if args.command == "balance":
        check_balance()
    elif args.command == "buy":
        buy_credits(args.quantity, args.amount)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
