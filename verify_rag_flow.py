import requests
import time
import sys
import io

# Force UTF-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_test():
    print("🚀 Starting RAG Flow Verification...")

    # 1. Login
    print("🔑 Authenticating...")
    # Register/Login
    email = f"test_{int(time.time())}@example.com"
    pwd = "password123"
    requests.post(f"{BASE_URL}/auth/signup", json={"email": email, "password": pwd})
    r = requests.post(f"{BASE_URL}/auth/token", data={"username": email, "password": pwd})
    if r.status_code != 200:
        print(f"❌ Login Failed: {r.text}")
        return
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login Success")

    # 2. Upload Global Doc
    print("🌍 Uploading Global Document...")
    global_content = "The Secret Global Key is OMEGA-99."
    files = {'file': ('global_secret.md', global_content)}
    r = requests.post(f"{BASE_URL}/conversations/documents/global", headers=headers, files=files)
    if r.status_code != 200:
        print(f"❌ Global Upload Failed: {r.text}")
    else:
        print(f"✅ Global Upload Success: {r.json()}")

    # 3. Create Conversation
    print("💬 Creating Conversation A...")
    r = requests.post(f"{BASE_URL}/conversations/", headers=headers)
    convo_id = r.json()["convo_id"]
    print(f"   ID: {convo_id}")

    # 4. Upload Convo Doc
    print("📂 Uploading Private Document to Convo A...")
    convo_content = "The Private Code for A is ALPHA-11."
    files = {'file': ('private_secret.md', convo_content)}
    r = requests.post(f"{BASE_URL}/conversations/{convo_id}/documents", headers=headers, files=files)
    if r.status_code != 200:
        print(f"❌ Private Upload Failed: {r.text}")
    else:
        print(f"✅ Private Upload Success: {r.json()}")

    # 5. Test Retrieval (RAG)
    print("❓ Asking Convo A about Global Key...")
    q1 = "What is the Global Key?"
    r = requests.post(f"{BASE_URL}/conversations/{convo_id}/ask", headers=headers, json={"message": q1})
    ans1 = r.json().get("answer", "")
    citations1 = r.json().get("citations", [])
    print(f"   Answer: {ans1}")
    print(f"   Citations: {[c['source'] for c in citations1]}")

    print("❓ Asking Convo A about Private Code...")
    q2 = "What is the Private Code?"
    r = requests.post(f"{BASE_URL}/conversations/{convo_id}/ask", headers=headers, json={"message": q2})
    ans2 = r.json().get("answer", "")
    citations2 = r.json().get("citations", [])
    print(f"   Answer: {ans2}")
    print(f"   Citations: {[c['source'] for c in citations2]}")

    # 6. Verify Isolation (Convo B)
    print("💬 Creating Conversation B (Should NOT see Private Code A)...")
    r = requests.post(f"{BASE_URL}/conversations/", headers=headers)
    convo_b = r.json()["convo_id"]
    
    print("❓ Asking Convo B about Private Code (Should fail)...")
    r = requests.post(f"{BASE_URL}/conversations/{convo_b}/ask", headers=headers, json={"message": q2})
    ans3 = r.json().get("answer", "")
    citations3 = r.json().get("citations", [])
    print(f"   Answer: {ans3}")
    print(f"   Citations: {[c['source'] for c in citations3]}")

if __name__ == "__main__":
    run_test()
