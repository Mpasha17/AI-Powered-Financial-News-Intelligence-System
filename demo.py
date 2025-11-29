import requests
import time
import sys
import json

BASE_URL = "http://localhost:8000/api"

def print_header(text):
    print("\n" + "="*50)
    print(f" {text}")
    print("="*50 + "\n")

def run_demo():
    print_header("Starting Financial News Intelligence Demo")
    
    # 1. Ingest Data
    print("Step 1: Triggering Real RSS Ingestion...")
    try:
        response = requests.post(f"{BASE_URL}/ingest")
        if response.status_code == 200:
            print(f"  - {response.json()['message']}")
        else:
            print(f"  - Error: {response.text}")
    except Exception as e:
        print(f"  - Failed to connect to API. Is it running? Error: {e}")
        return
    time.sleep(2) # Wait for processing
        
    # 2. Check Stats
    print("\nStep 2: Checking System Stats...")
    response = requests.get(f"{BASE_URL}/stats")
    print(json.dumps(response.json(), indent=2))
    
    # 3. Perform Queries
    queries = [
        "HDFC Bank news",
        "Banking sector update",
        "RBI policy changes"
    ]
    
    print("\nStep 3: Running Context-Aware Queries...")
    for q in queries:
        print(f"\nQuery: '{q}'")
        response = requests.get(f"{BASE_URL}/query", params={"q": q})
        data = response.json()
        
        print(f"  Expanded Context: {data['expanded_context']}")
        print(f"  Found {len(data['results'])} relevant articles:")
        for article in data['results']:
            print(f"    - [{article['source']}] {article['title']}")
            if article.get('impacted_stocks'):
                stocks = [f"{s['symbol']} ({s['confidence']})" for s in article['impacted_stocks']]
                print(f"      Impact: {', '.join(stocks)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "wait":
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(5)
    run_demo()
