import urllib.request
import json
import sys
import os

API_BASE = "http://localhost:5000"
TOKEN = ""  # Set your token here if using authentication

def call_api(endpoint, method="GET", data=None):
    """Generic function to call the FIM API."""
    url = f"{API_BASE}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    body = None
    if data:
        body = json.dumps(data).encode()
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(e.read().decode())
        return None
    except urllib.error.URLError as e:
        print(f"Connection Error: {e.reason}")
        return None


def menu():
    """Interactive API test menu."""
    while True:
        print("*"*50)
        print("FIM API TEST MENU")
        print("*"*50)
        print("1. Health Check")
        print("2. Get All Hashes")
        print("3. Get Single File Hash")
        print("4. Compare Baseline (from file)")
        print("5. View Event History")
        print("6. Exit")
        
        choice = input("Choose: ").strip()
        
        if choice == "1":
            result = call_api("/health")
            if result:
                print(f"Status: {result['status']}")
                print(f"Files monitored: {result['count']}")
        
        elif choice == "2":
            result = call_api("/hashes")
            if result:
                print(f"\nFiles found: {len(result)}")
                for path, hash_val in result.items():
                    print(f"  {path}: {hash_val[:16]}...")
        
        elif choice == "3":
            path = input("Enter file path (relative): ").strip()
            result = call_api(f"/hash?path={path}")
            if result:
                print(json.dumps(result, indent=2))
        
        elif choice == "4":
            baseline_path = input("Enter path to baseline.json: ").strip()
            if not os.path.exists(baseline_path):
                print("File not found!")
                continue
            with open(baseline_path, 'r') as f:
                baseline = json.load(f)
            result = call_api("/check", method="POST", data=baseline)
            if result:
                print("\nChanges detected:")
                print(f"  New: {result.get('new', [])}")
                print(f"  Deleted: {result.get('deleted', [])}")
                print(f"  Modified: {result.get('modified', [])}")
                if not any(result.values()):
                    print("  No changes detected.")
        
        elif choice == "5":
            limit = input("Number of events [20]: ").strip() or "20"
            result = call_api(f"/history?limit={limit}")
            if result:
                print(f"\nLast {len(result)} events:")
                for event in result:
                    print(f"  {event['timestamp']} | {event['event']:8} | {event['file']}")
        
        elif choice == "6":
            print("Goodbye.")
            break
        
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    menu()