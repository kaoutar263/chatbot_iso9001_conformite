import chromadb
from chromadb.config import Settings
import os

def inspect():
    # Attempt to connect to the persistence directory
    # Note: In Docker this is /app/data/chroma_db, locally it's ./data/chroma_db
    # We'll assume we are running this locally to inspect the volume mount
    db_path = "./data/chroma_db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database path not found at: {db_path}")
        return

    print(f"🔍 Inspecting ChromaDB at: {db_path}")
    
    try:
        client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        # Collections
        col_names = client.list_collections()
        print(f"📂 Collections found: {[c.name for c in col_names]}")
        
        if "iso_docs" not in [c.name for c in col_names]:
            print("   ⚠️ 'iso_docs' collection not found.")
            return

        collection = client.get_collection("iso_docs")
        count = collection.count()
        print(f"📄 Total Chunks in 'iso_docs': {count}")
        
        if count == 0:
            print("   ⚠️ Collection is empty.")
            return

        # Get all metadata to analyze sources
        # Chroma default limit is often small, set to None or count to get all
        data = collection.get(include=["metadatas"], limit=count)
        metadatas = data["metadatas"]
        
        stats = {}
        for m in metadatas:
            source = m.get("source", "Unknown")
            scope = m.get("scope", "Unknown")
            key = f"{source} (Scope: {scope})"
            stats[key] = stats.get(key, 0) + 1
            
        print("\n📊 Document Statistics:")
        print(f"{'Document Source':<50} | {'Scope':<20} | {'Chunks'}")
        print("-" * 85)
        for key, quantity in stats.items():
            src, scp = key.split(" (Scope: ")
            scp = scp.rstrip(")")
            print(f"{src:<50} | {scp:<20} | {quantity}")
            
        print("\n🔎 Checking for Excel files...")
        excel_found = False
        for key in stats:
            if ".xls" in key.lower():
                excel_found = True
                print(f"   ✅ Found Excel: {key}")
        
        if not excel_found:
            print("   ❌ No Excel files found in the database.")
            
    except Exception as e:
        print(f"❌ Error inspecting DB: {e}")

if __name__ == "__main__":
    inspect()
