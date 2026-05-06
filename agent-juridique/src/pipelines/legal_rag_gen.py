from src.tools.rag_researcher import RAGResearcher
from src.tools.legal_generator import LegalGenerator
from src.tools.legal_critic import LegalCritic

class LegalResponsePipeline:
    def __init__(self):
        # 1. TOOL METADATA (This is what the Master Agent reads)

        self.name = "tunisian_legal_researcher"
        self.description = (
            "Utile pour répondre à des questions complexes sur le droit tunisien. "
            "Cet outil effectue une recherche dans la base de données, rédige une réponse "
            "et la fait vérifier par un auditeur juridique pour garantir l'absence d'hallucinations."
        )
        # Tools
        self.researcher = RAGResearcher()
        self.generator = LegalGenerator()
        self.critic = LegalCritic()

    def run(self, query):
        # --- SHARED MEMORY / STATE ---
        state = {
            "query": query,
            "context": None,
            "drafts": [],      # List of all drafts produced
            "critiques": [],   # List of all critiques received
            "final_score": 0,
            "status": "in_progress"
        }

        # Step 1: Retrieval
        print("🔍 Pipeline: Fetching legal context...")
        docs = self.researcher.juridical_search(state["query"])
        state["context"] = "\n".join([d['text'] for d in docs])

        # Step 2: Iterative Generation & Critique (The Loop)
        for i in range(3):
            print(f"🔄 Pipeline: Iteration {i+1}")
            
            # Shared memory: Provide the last feedback if it exists
            last_feedback = state["critiques"][-1]["critique"] if state["critiques"] else ""
            
            # Action: Generate
            new_draft = self.generator.execute(
                state["query"], 
                state["context"], 
                last_feedback
            )
            state["drafts"].append(new_draft)

            # Action: Critique
            audit_report = self.critic.execute(
                state["query"], 
                state["context"], 
                new_draft
            )
            state["critiques"].append(audit_report)
            state["final_score"] = audit_report["score"]

            # Exit condition
            if audit_report["approved"] or audit_report["score"] >= 0.95:
                state["status"] = "completed"
                print("✅ Pipeline: Quality threshold reached.")
                break
        
        # Return the last successful draft
        return state["drafts"][-1]