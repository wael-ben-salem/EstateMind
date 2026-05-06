import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from dotenv import load_dotenv

load_dotenv()

def get_qdrant_client():
    return QdrantClient(
        url=os.getenv("QDRANT_URL"), 
        api_key=os.getenv("QDRANT_API_KEY")
    )

def setup_collection(collection_name="tunisian_laws", force_recreate=False):
    client = get_qdrant_client()

    if force_recreate and client.collection_exists(collection_name):
        print(f"🗑️ Deleting existing collection: {collection_name}")
        client.delete_collection(collection_name)

    if not client.collection_exists(collection_name):
        print(f"🏗️ Creating collection: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            # Cohere embed-multilingual-v3.0 uses 1024 dimensions
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
        print("✅ Collection ready.")
    else:
        print(f"ℹ️ Collection '{collection_name}' already exists. Skipping setup.")

if __name__ == "__main__":
    # Run this file directly to initialize your DB
    setup_collection(force_recreate=False)