import requests
import time
import sys
import io

# Force UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def verify():
    # Wait for server to be up (simple retry logic could be added here or manual wait)
    url = "http://127.0.0.1:8000/api/v1/conversations/test-uuid/ask"
    payload = {
        "message": "Qu'est-ce que la norme ISO 9001 ?",
        "settings": {
            "model": "llama-3.3-70b-versatile"
        }
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        print("\n✅ Verification Successful!")
        print("FULL RESPONSE:")
        print(data)
        print("----------------")
        print(f"Answer: {data.get('answer')}")
        print(f"Citations found: {len(data.get('citations', []))}")
        for cit in data.get('citations', []):
            print(f"- Source: {cit.get('source')}")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        if hasattr(e, 'response') and e.response:
             print(f"Response: {e.response.text}")

if __name__ == "__main__":
    verify()
