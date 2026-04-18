import chromadb
from config import settings

def inspect_chroma():
    print(f"🔍 Connecting to ChromaDB at: {settings.chroma_persist_dir}")
    
    # Initialize the client
    client = chromadb.PersistentClient(path=str(settings.chroma_persist_dir))
    
    # List collections
    collections = client.list_collections()
    print(f"📊 Collections found: {[c.name for c in collections]}")
    
    if not collections:
        print("❌ No collections found in this database.")
        return

    # Choose the main 'documents' collection
    collection_name = "documents"
    try:
        collection = client.get_collection(name=collection_name)
        count = collection.count()
        print(f"📑 Collection '{collection_name}' has {count} chunks.")
        
        if count == 0:
            print("📭 The collection is empty.")
            return

        # Fetch all data (limit to 100 for safety)
        results = collection.get(
            include=["documents", "metadatas"]
        )
        
        print("\n--- Document Chunks ---")
        for i in range(len(results["ids"])):
            doc_id = results["ids"][i]
            content = results["documents"][i]
            metadata = results["metadatas"][i]
            
            print(f"\n🆔 ID: {doc_id}")
            print(f"📄 Filename: {metadata.get('filename', 'Unknown')}")
            print(f"👤 User ID: {metadata.get('uid', 'Unknown')}")
            print(f"📝 Content Snippet: {content[:150]}...")
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ Error accessing collection '{collection_name}': {e}")

if __name__ == "__main__":
    inspect_chroma()
