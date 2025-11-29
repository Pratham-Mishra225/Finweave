"""
Test script for Transactions API endpoints.

Run this after starting the server to verify all endpoints work correctly.
Requires a valid Firebase ID token.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
# Replace with a valid Firebase ID token
FIREBASE_TOKEN = "YOUR_FIREBASE_ID_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {FIREBASE_TOKEN}",
    "Content-Type": "application/json"
}


def test_create_transaction():
    """Test POST /transactions"""
    print("\n1. Testing: Create Transaction")
    transaction = {
        "name": "Grocery Shopping",
        "amount": 50.75,
        "type": "expense",
        "category": "Food",
        "description": "Weekly groceries",
        "date": datetime.utcnow().isoformat(),
        "recurring": False
    }
    
    response = requests.post(
        f"{BASE_URL}/transactions",
        headers=headers,
        json=transaction
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"Created transaction ID: {data['id']}")
        return data['id']
    else:
        print(f"Error: {response.text}")
        return None


def test_get_transactions():
    """Test GET /transactions"""
    print("\n2. Testing: Get Transactions (Paginated)")
    response = requests.get(
        f"{BASE_URL}/transactions?page=1&limit=10",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total transactions: {data['total']}")
        print(f"Page {data['page']} of {data['pages']}")
        print(f"Transactions in this page: {len(data['transactions'])}")
    else:
        print(f"Error: {response.text}")


def test_search_transactions():
    """Test GET /transactions/search"""
    print("\n3. Testing: Search Transactions")
    response = requests.get(
        f"{BASE_URL}/transactions/search?q=Grocery&page=1&limit=10",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['total']} matching transactions")
    else:
        print(f"Error: {response.text}")


def test_filter_transactions():
    """Test GET /transactions/filter"""
    print("\n4. Testing: Filter Transactions")
    response = requests.get(
        f"{BASE_URL}/transactions/filter?category=Food&type=expense&page=1&limit=10",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['total']} matching transactions")
    else:
        print(f"Error: {response.text}")


def test_get_summary():
    """Test GET /transactions/summary"""
    print("\n5. Testing: Get Transaction Summary")
    response = requests.get(
        f"{BASE_URL}/transactions/summary",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total Income: ${data['total_income']:.2f}")
        print(f"Total Expenses: ${data['total_expenses']:.2f}")
        print(f"Net Balance: ${data['net_balance']:.2f}")
        print(f"Transaction Count: {data['transaction_count']}")
        print(f"Top Category: {data['top_category']} (${data.get('top_category_amount', 0):.2f})")
    else:
        print(f"Error: {response.text}")


def test_get_transaction(transaction_id):
    """Test GET /transactions/{id}"""
    if not transaction_id:
        print("\n6. Skipping: Get Transaction by ID (no transaction created)")
        return
    
    print(f"\n6. Testing: Get Transaction by ID ({transaction_id})")
    response = requests.get(
        f"{BASE_URL}/transactions/{transaction_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Transaction: {data['name']} - ${data['amount']}")
    else:
        print(f"Error: {response.text}")


def test_update_transaction(transaction_id):
    """Test PUT /transactions/{id}"""
    if not transaction_id:
        print("\n7. Skipping: Update Transaction (no transaction created)")
        return
    
    print(f"\n7. Testing: Update Transaction ({transaction_id})")
    update = {
        "amount": 55.00,
        "description": "Updated weekly groceries"
    }
    
    response = requests.put(
        f"{BASE_URL}/transactions/{transaction_id}",
        headers=headers,
        json=update
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Updated: {data['name']} - ${data['amount']}")
    else:
        print(f"Error: {response.text}")


def test_delete_transaction(transaction_id):
    """Test DELETE /transactions/{id}"""
    if not transaction_id:
        print("\n8. Skipping: Delete Transaction (no transaction created)")
        return
    
    print(f"\n8. Testing: Delete Transaction ({transaction_id})")
    response = requests.delete(
        f"{BASE_URL}/transactions/{transaction_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 204:
        print("Transaction deleted successfully")
    else:
        print(f"Error: {response.text}")


def main():
    print("=" * 60)
    print("TRANSACTIONS API TEST SUITE")
    print("=" * 60)
    
    if FIREBASE_TOKEN == "YOUR_FIREBASE_ID_TOKEN_HERE":
        print("\n⚠️  ERROR: Please set a valid Firebase ID token in the script!")
        print("Get a token by logging in through the frontend app or Firebase Auth.")
        return
    
    # Test all endpoints
    transaction_id = test_create_transaction()
    test_get_transactions()
    test_search_transactions()
    test_filter_transactions()
    test_get_summary()
    test_get_transaction(transaction_id)
    test_update_transaction(transaction_id)
    test_delete_transaction(transaction_id)
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
