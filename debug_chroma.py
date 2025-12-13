import chromadb
from chromadb.config import Settings
import os

print(f"CWD: {os.getcwd()}")
abs_path = os.path.abspath("./data/chroma_db")
print(f"Abs Path to DB dir: {abs_path}")
print(f"Exists: {os.path.exists(os.path.join(abs_path, 'chroma.sqlite3'))}")

try:
    client = chromadb.PersistentClient(
        path="./data/chroma_db",
        settings=Settings(anonymized_telemetry=False)
    )
    print("Client created")
    cols = client.list_collections()
    print(f"Collections listed: {cols}")
    col = client.get_collection("iso_docs")
    print(f"Collection count: {col.count()}")
except Exception as e:
    import traceback
    traceback.print_exc()
