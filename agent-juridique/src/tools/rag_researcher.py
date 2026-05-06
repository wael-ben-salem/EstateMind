import os
import cohere
from qdrant_client import QdrantClient
from src.ingestion.setup_db import get_qdrant_client
from dotenv import load_dotenv

load_dotenv()

class RAGResearcher:
    def __init__(self, collection_name="tunisian_laws"):
        self.co = cohere.Client(os.getenv("COHERE_API_KEY"))
        self.qdrant = get_qdrant_client()
        self.collection_name = collection_name

    def search_and_rerank(self, query, top_k=15, rerank_top_n=5):
        """
        1. Embeds query
        2. Searches Qdrant for top_k candidates
        3. Reranks candidates down to rerank_top_n
        """
        
        # --- STEP 1: EMBED THE QUERY ---
        # Note: input_type must be "search_query" for retrieval
        query_vector = self.co.embed(
            texts=[query],
            model="embed-multilingual-v3.0",
            input_type="search_query"
        ).embeddings[0]

        # --- STEP 2: INITIAL QDRANT SEARCH ---
        search_result = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True
        ).points

        if not search_result:
            print("⚠️ No matches found in database.")
            return []

        # Extract text for the reranker
        documents = [hit.payload["text"] for hit in search_result]

        # --- STEP 3: COHERE RERANK ---
        print(f"🔄 Reranking top {len(documents)} candidates...")
        rerank_results = self.co.rerank(
            query=query,
            documents=documents,
            top_n=rerank_top_n,
            model="rerank-multilingual-v3.0"
        ).results

        # --- STEP 4: RECONSTRUCT DATA ---
        final_results = []
        for result in rerank_results:
            # Map index back to the original Qdrant hit
            original_hit = search_result[result.index]
            
            final_results.append({
                "id": original_hit.payload.get('article_number'),
                "text": original_hit.payload.get('text'),
                "context": original_hit.payload.get('keyword'),
                "source": original_hit.payload.get('source'),
                "rerank_score": result.relevance_score
            })

        return final_results

# Example Usage for Testing
if __name__ == "__main__":
    researcher = RAGResearcher()
    question = "Quels sont les droits d'un mineur dans un contrat ?"
    
    results = researcher.search_and_rerank(question)
    
    for i, res in enumerate(results):
        print(f"\n--- Result {i+1} (Score: {res['rerank_score']:.4f}) ---")
        print(f"📍 Location: {res['context']} (Source: {res['source']})")
        print(f"📖 Text: {res['text'][:200]}...")
        
print ("✅ RAGResearcher class defined successfully.")