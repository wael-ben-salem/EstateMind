import os
import json
import time
from typing import Dict, List, Optional, Any
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
from dotenv import load_dotenv

from src.tools.rag_researcher import RAGResearcher
from src.tools.legal_critic import LegalCritic
from src.tools.doc_analyzer import DocumentAnalyzer
from src.utils.logger import get_logger

load_dotenv(override=True)

logger = get_logger(__name__)

class RAGAgent:
    def __init__(
        self,
        max_iterations: int = 5,
        max_context_size: int = 50,
        context_chunk_size: int = 500,
        api_timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the RAG Agent with configurable parameters.
        
        Args:
            max_iterations: Maximum number of reasoning iterations
            max_context_size: Maximum number of context snippets to keep
            context_chunk_size: Size of text chunks to store (characters)
            api_timeout: Timeout for API calls (seconds)
            max_retries: Maximum number of retries for failed API calls
        """
        logger.info("Initializing RAGAgent with configuration: max_iterations=%d, max_context_size=%d, context_chunk_size=%d, api_timeout=%d, max_retries=%d",
                max_iterations, max_context_size, context_chunk_size, api_timeout, max_retries)
        
        self.max_iterations = max_iterations
        self.max_context_size = max_context_size
        self.context_chunk_size = context_chunk_size
        self.api_timeout = api_timeout
        self.max_retries = max_retries
        
        try:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_3"),
                timeout=api_timeout
            )
            self.model = "openai/gpt-oss-120b:free"
            logger.info("OpenAI client initialized successfully with model: %s", self.model)
        except Exception as e:
            logger.error("Failed to initialize OpenAI client: %s", str(e), exc_info=True)
            raise

        # Specialized Tools
        try:
            self.retriever = RAGResearcher()
            self.critic = LegalCritic()
            self.analyzer = DocumentAnalyzer()
            logger.debug("RAG tools (retriever, critic and analyzer) initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize RAG tools: %s", str(e), exc_info=True)
            raise

        # Knowledge Base & Memory
        self.memory = {
            "accumulated_context": [],  # List of text snippets found
            "drafts": [],               # History of drafts
            "steps": [],                # Step-by-step history
            "search_queries": []        # Previous search inputs
        }
        
        logger.info("RAGAgent initialized successfully")

    def _get_reasoning_prompt(self, user_query: str, chat_history: list = None) -> str:
        if chat_history is None:
            chat_history = []

        session_preview = chat_history[-4:]
        history_str = "\n".join([f"{m['role'].upper()}: {m['content'][:300]}..." for m in session_preview])
        
        context_preview = self.memory["accumulated_context"][-5:]
        context_str = json.dumps(context_preview, ensure_ascii=False)
        
        return f"""
        Tu es un Agent Juridique Expert spécialisé en DROIT IMMOBILIER TUNISIEN.
        
        ### RÈGLES DE PORTÉE (SCOPE) :
        1. **Questions Générales / Salutations** : (ex: "Bonjour", "Comment ça va ?") -> Réponds poliment et directement.
        2. **Hors-Sujet** : Si la question n'a AUCUN rapport avec le droit ou l'immobilier (ex: "Qui a gagné le match ?", "Donne moi une recette"), réponds poliment que tu es un assistant spécialisé en droit immobilier tunisien et que tu ne peux pas répondre à cela.
        3. **Questions Juridiques** : Utilise le cycle SEARCH -> DRAFT.

        OUTILS :
        1. "SEARCH" : Rechercher dans la base de données légale.
        2. "DRAFT" : Rédiger la réponse en lisant les lois/documents en mémoire. (IMPORTANT : Si le 'Nombre de lois en mémoire' > 0, tu DOIS choisir cette action pour avoir accès au texte du document).
        3. "FINAL_SUBMIT" : Utilise cette action pour donner la réponse finale à l'utilisateur.

        ### COMMENT RÉPONDRE DIRECTEMENT :
        Si la question est une salutation ou hors-sujet :
        - Action : "FINAL_SUBMIT"
        - Action_input : "Ta réponse polie ici"

        ÉTAT ACTUEL :
        - Question : {user_query}
        - Nombre de lois en mémoire : {len(self.memory["accumulated_context"])}
        - Dernier brouillon : {self.memory["drafts"][-1][:300] + '...' if self.memory['drafts'] else 'Aucun brouillon'}
        - Historique : {history_str}

        RÉPOND UNIQUEMENT EN JSON :
        {{
            "thought": "Est-ce une question juridique immobilière ou une simple salutation ?",
            "action": "SEARCH" | "DRAFT" | "FINAL_SUBMIT",
            "action_input": "La requête ou ta réponse directe"
        }}
        """

    def _call_llm_with_retry(self, prompt: str, system_message: str, json_mode: bool = False) -> Dict[str, Any]:
        """
        Call LLM with retry logic and error handling.
        
        Args:
            prompt: User prompt
            system_message: System message
            json_mode: Whether to use JSON response format
            
        Returns:
            Parsed response as dictionary
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug("Calling LLM (attempt %d/%d)", attempt + 1, self.max_retries)
                
                kwargs = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0
                }
                
                # Removed response_format as many OpenRouter free models do not support it and return broken responses.
                
                response = self.client.chat.completions.create(**kwargs)
                
                # BULLETPROOF SAFETY CHECK:
                if not response or not hasattr(response, "choices") or not response.choices:
                    logger.error("Invalid API response received from OpenRouter. Raw: %s", response)
                    raise ValueError("The LLM server returned an empty or broken response.")
                    
                content = response.choices[0].message.content
                
                if not content:
                    raise ValueError("The LLM returned empty text.")
                
                if json_mode:
                    try:
                        # Clean up potential markdown formatting like ```json ... ```
                        clean_content = content.strip()
                        if clean_content.startswith("```json"):
                            clean_content = clean_content[7:]
                        elif clean_content.startswith("```"):
                            clean_content = clean_content[3:]
                        if clean_content.endswith("```"):
                            clean_content = clean_content[:-3]
                            
                        # Find the first { and last } to extract JSON
                        start_idx = clean_content.find('{')
                        end_idx = clean_content.rfind('}')
                        if start_idx != -1 and end_idx != -1:
                            clean_content = clean_content[start_idx:end_idx+1]
                            
                        parsed = json.loads(clean_content)
                        logger.debug("LLM response parsed successfully")
                        return parsed
                    except json.JSONDecodeError as e:
                        logger.warning("JSON parsing failed on attempt %d: %s. Response: %s", attempt + 1, str(e), content[:200])
                        if attempt < self.max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        raise ValueError(f"Failed to parse JSON after {self.max_retries} attempts")
                else:
                    return {"content": content}
                    
            except (APIConnectionError, APITimeoutError) as e:
                logger.warning("API connection error on attempt %d: %s", attempt + 1, str(e))
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
            except APIError as e:
                logger.error("API error: %s", str(e), exc_info=True)
                raise

    def _generate_draft(self, user_query: str, context: List[Dict], chat_history: List[Dict] = None) -> str:
        """
        Generate a draft response using the LLM based on accumulated context.
        
        Args:
            user_query: Original user question
            context: List of context snippets
            chat_history: List of previous messages in the conversation
        
            
        Returns:
            Generated draft text
        """
        if chat_history is None:
            chat_history = []
        logger.info("Generating draft for query: %s", user_query[:100])
        
        history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in chat_history[-3:]])
        context_text = "\n".join([f"[{c.get('id', 'unknown')}] {c.get('text', '')}" for c in context])        
        draft_prompt = f"""
        Tu es un expert juridique tunisien. Base-toi UNIQUEMENT sur le contexte fourni pour rédiger une réponse complète, structurée et bien rédigée.
        
        QUESTION: {user_query}
        
        ### HISTORIQUE DE LA CONVERSATION :
        {history_str if history_str else "Premier échange."}
        
        CONTEXTE DISPONIBLE:
        {context_text}
        
        RÉDIGE UNE RÉPONSE COMPLÈTE ET STRUCTURÉE.
        """
        
        try:
            response = self._call_llm_with_retry(
                draft_prompt,
                "Tu es un expert juridique tunisien senior. Rédige des réponses claires, complètes et bien structurées.",
                json_mode=False
            )
            draft = response.get("content", "")
            logger.info("Draft generated successfully (length: %d characters)", len(draft))
            return draft
        except Exception as e:
            logger.error("Failed to generate draft: %s", str(e), exc_info=True)
            raise

    def _manage_context_size(self):
        """Remove oldest context items if memory exceeds max_context_size."""
        if len(self.memory["accumulated_context"]) > self.max_context_size:
            removed_count = len(self.memory["accumulated_context"]) - self.max_context_size
            self.memory["accumulated_context"] = self.memory["accumulated_context"][-self.max_context_size:]
            logger.debug("Trimmed %d old context items to maintain max size of %d", removed_count, self.max_context_size)

    def ask(self, user_query, chat_history=None):
        """
        Process a legal query through the agentic reasoning loop.
        
        Args:
            user_query: The legal question to answer
            
        Returns:
            Final generated response or error message
        """ 
        # Validate input
        if not user_query or not isinstance(user_query, str):
            logger.error("Invalid user query: must be a non-empty string")
            raise ValueError("User query must be a non-empty string")
        
        user_query = user_query.strip()
        logger.info("Starting reasoning loop for query: %s", user_query[:100])
        
        try:
            search_attempts = 0
            for iteration in range(1, self.max_iterations + 1):
                logger.info("=== Iteration %d/%d ===", iteration, self.max_iterations)
                
                # 1. THINK - Call LLM for reasoning
                try:
                    prompt = self._get_reasoning_prompt(user_query, chat_history)
                    decision = self._call_llm_with_retry(
                        prompt,
                        "Tu es un agent juridique méthodique et analytique.",
                        json_mode=True
                    )
                except Exception as e:
                    logger.error("Failed to get reasoning decision: %s", str(e), exc_info=True)
                    raise
                
                thought = decision.get("thought", "")
                action = decision.get("action", "").upper()
                action_input = decision.get("action_input", "")
                
                logger.info("Decision: action=%s, thought=%s", action, thought[:100])
                logger.debug("Action input: %s", str(action_input)[:200])

                if action == "SEARCH":
                    if action_input.strip().lower() in [q.strip().lower() for q in self.memory["search_queries"]]:
                        logger.info("Search query duplicated, switching to DRAFT to avoid repeated searches.")
                        action = "DRAFT"
                    elif search_attempts >= 1 and self.memory["accumulated_context"]:
                        logger.info("Multiple SEARCH attempts detected, switching to DRAFT to reduce suspicious repetition.")
                        action = "DRAFT"
                    else:
                        search_attempts += 1
                        self.memory["search_queries"].append(action_input)

                elif action == "DRAFT" and not self.memory["accumulated_context"]:
                    logger.info("No context available for DRAFT, switching to SEARCH to gather information.")
                    action = "SEARCH"

                elif action == "FINAL_SUBMIT" and self.memory["accumulated_context"] and not self.memory["drafts"]:
                    logger.info("LLM attempted FINAL_SUBMIT but context is available. Forcing DRAFT so it reads the document/laws.")
                    action = "DRAFT"

                if action != decision.get("action", "").upper():
                    logger.info("Adjusted action to %s after heuristic processing.", action)

                # 2. ACT - Execute action
                if action == "SEARCH":
                    logger.info("Executing SEARCH with query: %s", action_input)
                    try:
                        results = self.retriever.search_and_rerank(action_input)
                        new_info = [
                            {
                                "id": r.get('id', f'doc_{i}'),
                                "text": r.get('text', '')[:self.context_chunk_size]
                            }
                            for i, r in enumerate(results)
                        ]
                        self.memory["accumulated_context"].extend(new_info)
                        self._manage_context_size()
                        
                        logger.info("Search completed: %d new results added (total context: %d)",
                                    len(new_info), len(self.memory["accumulated_context"]))
                        logger.info("New context items: %s", [item['text'][:100] + "..." for item in new_info])
                        self.memory["steps"].append(f"Iteration {iteration}: Recherche sur '{action_input}' → {len(new_info)} résultats")
                        
                    except Exception as e:
                        logger.error("Search failed: %s", str(e), exc_info=True)
                        self.memory["steps"].append(f"Iteration {iteration}: Erreur de recherche")
                        raise

                elif action == "DRAFT":
                    logger.info("Executing DRAFT")
                    try:
                        draft = self._generate_draft(user_query, self.memory["accumulated_context"], chat_history)
                        self.memory["drafts"].append(draft)
                        logger.info("Draft created successfully (length: %d)", len(draft))
                        self.memory["steps"].append(f"Iteration {iteration}: Brouillon rédigé ({len(draft)} chars)")

                        # logger.info("Automatically auditing the draft after creation.")
                        # context_text = "\n".join([
                        #     f"[{c.get('id', 'unknown')}] {c.get('text', '')}"
                        #     for c in self.memory["accumulated_context"][-10:]
                        # ])
                        # report = self.critic.audit(user_query, context_text, draft)
                        # self.memory["audit_feedback"] = report

                        # score = report.get("score", 0)
                        # approved = report.get("approved", False)
                        # critique = report.get("critique", "")
                        # instructions = report.get("instructions", "")

                        # logger.info("Auto-audit completed: score=%.2f, approved=%s", score, approved)
                        # logger.debug("Critique: %s", critique[:200])
                        # logger.debug("Instructions: %s", instructions[:200])
                        # self.memory["steps"].append(
                        #     f"Iteration {iteration}: Audit après brouillon → Score: {score:.2f}, Approuvé: {approved}"
                        # )

                        # if approved:
                        #     logger.info("Draft approved by audit, submitting final result.")
                        #     self.memory["steps"].append(f"Iteration {iteration}: Brouillon approuvé, soumission finale")
                        #     return draft
                        # else:
                        #     logger.warning("Draft rejected. Critique: %s", critique[:200])
                        #     self.memory["steps"].append(f"Iteration {iteration}: Brouillon rejeté, continuer")
                        #     continue
                        
                        logger.info("Audit disabled. Returning draft directly.")
                        self.memory["steps"].append(f"Iteration {iteration}: Brouillon soumis directement (Audit désactivé)")
                        return draft

                    except Exception as e:
                        logger.error("Draft generation or audit failed: %s", str(e), exc_info=True)
                        self.memory["steps"].append(f"Iteration {iteration}: Erreur de rédaction/audit")
                        raise

                

                # elif action == "AUDIT":
                #     logger.info("Executing AUDIT")
                #     try:
                #         if not self.memory["drafts"]:
                #             logger.warning("No drafts to audit, skipping AUDIT action")
                #             self.memory["steps"].append(f"Iteration {iteration}: Pas de brouillon à auditer")
                #             continue
                #         
                #         current_draft = self.memory["drafts"][-1]
                #         context_text = "\n".join([
                #             f"[{c.get('id', 'unknown')}] {c.get('text', '')}"
                #             for c in self.memory["accumulated_context"][-10:]  # Use last 10 items
                #         ])
                #         
                #         logger.debug("Sending to critic: query=%s, context_len=%d, draft_len=%d",
                #                     user_query[:50], len(context_text), len(current_draft))
                #         
                #         report = self.critic.audit(user_query, context_text, current_draft)
                #         self.memory["audit_feedback"] = report
                #         
                #         score = report.get("score", 0)
                #         approved = report.get("approved", False)
                #         critique = report.get("critique", "")
                #         instructions = report.get("instructions", "")
                #         
                #         logger.info("Audit completed: score=%.2f, approved=%s", score, approved)
                #         logger.debug("Critique: %s", critique[:200])
                #         logger.debug("Instructions: %s", instructions[:200])
                #         
                #         self.memory["steps"].append(
                #             f"Iteration {iteration}: Audit → Score: {score:.2f}, Approuvé: {approved}"
                #         )
                #         
                #         if approved and self.memory["drafts"]:
                #             logger.info("Audit approved, submitting final result.")
                #             self.memory["steps"].append(f"Iteration {iteration}: Audit approuvé, soumission finale")
                #             return self.memory["drafts"][-1]
                #         elif not approved:
                #             logger.warning("Audit rejected. Critique: %s", critique[:100])
                #         
                #     except Exception as e:
                #         logger.error("Audit failed: %s", str(e), exc_info=True)
                #         self.memory["steps"].append(f"Iteration {iteration}: Erreur d'audit")
                #         raise

                elif action == "FINAL_SUBMIT":
                    logger.info("Executing FINAL_SUBMIT")
                    
                    # 1. Priorité au brouillon audité (si existant)
                    if self.memory["drafts"]:
                        final_result = self.memory["drafts"][-1]
                        self.memory["steps"].append(f"Iteration {iteration}: Soumission du brouillon final.")
                        return final_result
                    
                    # 2. Check for direct conversational response
                    elif action_input and action_input.strip().lower() != "n/a":
                        logger.info("Direct response provided via action_input")
                        self.memory["steps"].append(f"Iteration {iteration}: Réponse directe fournie.")
                        return action_input
                    
                    # 3. RETRY LOGIC: If neither exists, force the agent to try again
                    else:
                        logger.warning("FINAL_SUBMIT called incorrectly (no content). Retrying iteration...")
                        self.memory["steps"].append(
                            f"Iteration {iteration}: Erreur - Tu as tenté un FINAL_SUBMIT sans fournir de texte dans 'action_input' et sans avoir rédigé de 'DRAFT'. Merci de rédiger une réponse ou de faire une recherche."
                        )
                        # We do NOT return anything. We let the loop continue to the next iteration.
                        continue
                
                else:
                    logger.warning("Unknown action: %s", action)
                    self.memory["steps"].append(f"Iteration {iteration}: Action inconnue '{action}'")

            logger.warning("Reached maximum iterations (%d) without finalizing", self.max_iterations)
            default_response = "L'agent n'a pas pu finaliser une réponse satisfaisante après {} itérations.".format(self.max_iterations)
            self.memory["steps"].append("Arrêt: Nombre maximum d'itérations atteint")
            return default_response

        except Exception as e:
            logger.error("Fatal error in ask() method: %s", str(e), exc_info=True)
            error_msg = f"Erreur de l'agent: {str(e)}"
            self.memory["steps"].append(f"Erreur fatale: {str(e)}")
            raise



if __name__ == "__main__":
    try:
        logger.info("Starting RAG Agent test")
        agent = RAGAgent(max_iterations=5, max_context_size=50)
        
        query = "Quelles sont les obligations d'un tuteur légal pour un mineur en Tunisie ? Cherche aussi les sanctions en cas de manquement."
        logger.info("Processing query: %s", query)
        
        result = agent.ask(query)
        
        logger.info("=== FINAL RESULT ===")
        print("\n" + "="*80)
        print(result)
        print("="*80)
        
        # Log memory summary
        logger.info("Agent memory summary - Total context: %d, Total drafts: %d, Total steps: %d",
                len(agent.memory["accumulated_context"]),
                len(agent.memory["drafts"]),
                len(agent.memory["steps"]))
                
    except Exception as e:
        logger.critical("Fatal error in main: %s", str(e), exc_info=True)
        raise