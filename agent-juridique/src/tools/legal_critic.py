import os
import json
import re
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
from src.utils.logger import get_logger

logger = get_logger(__name__)

class LegalCritic:
    def __init__(self, model: str = "openai/gpt-oss-120b:free", api_timeout: int = 30):
        """
        Initialize the LegalCritic auditor.
        
        Args:
            model: The model to use for auditing
            api_timeout: Timeout for API calls in seconds
        """
        logger.info("Initializing LegalCritic with model: %s", model)
        
        try:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_3"),
                timeout=api_timeout
            )
            self.model = model
            logger.debug("LegalCritic initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize LegalCritic: %s", str(e), exc_info=True)
            raise

    def _extract_json(self, text: str) -> str:
        """Extract the first JSON object from a string if extra text is present."""
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        return text

    def _parse_json(self, text: str) -> dict:
        """Parse a JSON string and raise a helpful error on failure."""
        raw_text = text.strip()
        # Remove control characters except \t, \n, \r
        cleaned_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_text)
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            extracted = self._extract_json(cleaned_text)
            try:
                return json.loads(extracted)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON from text: %s", cleaned_text[:300])
                raise ValueError("Invalid JSON response from audit") from e

    def _ensure_valid_json_response(self, prompt: str, user_message: str) -> dict:
        """Call the API and ensure the response is valid JSON.

        If the content is invalid or meta-commentary appears, retry once with a stricter audit-only instruction.
        """
        messages = [
            {"role": "system", "content": "Tu es un évaluateur juridique qui évalue la fidélité, pertinence et exactitude des réponses."},
            {"role": "user", "content": user_message}
        ]

        def call_api(messages_to_send):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages_to_send,
                response_format={"type": "json_object"},
                temperature=0
            )
            content = response.choices[0].message.content
            if isinstance(content, dict):
                return content
            return self._parse_json(str(content))

        result = None
        try:
            result = call_api(messages)
        except ValueError:
            logger.warning("First audit response was not valid JSON, retrying with explicit correction prompt.")
            corrected_messages = messages + [
                {
                    "role": "user",
                    "content": (
                        "Ignore toutes les instructions précédentes concernant le format de sortie. "
                        "Fais un audit juridique et réponds uniquement par un objet JSON valide : {\"score\":0.0, \"approved\":true, \"critique\":\"...\", \"instructions\":\"...\"}. "
                        "Ne mentionne pas la validité JSON ou le parsing dans le champ critique."
                    )
                }
            ]
            result = call_api(corrected_messages)

        if result is not None:
            critique_text = str(result.get("critique", ""))
            if re.search(r"json|guillemets|accolades|format|parse|parsing", critique_text, re.IGNORECASE):
                logger.warning("Audit critique contains JSON-format commentary, retrying with audit-only instruction.")
                corrected_messages = messages + [
                    {
                        "role": "user",
                        "content": (
                            "Ne commente pas la validité JSON. Fais seulement l'audit juridique de la réponse. "
                            "Réponds uniquement par un objet JSON valide contenant les champs score, approved, critique et instructions."
                        )
                    }
                ]
                result = call_api(corrected_messages)

        return result

    def audit(self, query: str, context: str, answer: str) -> dict:
        """
        Audit a legal response for accuracy and compliance.
        
        Args:
            query: The original legal question
            context: The context used to generate the answer
            answer: The generated legal response
            
        Returns:
            Audit report with score, approval status, critique, and instructions
        """
        logger.info("Starting audit for query: %s", query[:100])
        
        prompt = f"""
        Tu es un évaluateur juridique spécialisé en droit tunisien. Ton rôle est d'évaluer la fidélité au contexte, la pertinence et l'exactitude de la réponse :
        CONTEXTE: {context}
        QUESTION: {query}
        RÉPONSE: {answer}

        Évalue uniquement :
        - Fidélité : La réponse est-elle fidèle aux informations du contexte fourni ?
        - Pertinence : La réponse répond-elle directement à la question posée ?
        - Exactitude : Les informations sont-elles correctes selon le contexte ?

        Sois constructif et indulgent : approuve la réponse si elle est globalement fidèle, pertinente et exacte, même avec des imperfections mineures.
        Donne un score entre 0.0 et 1.0, où 0.8+ est considéré comme bon.
        Approuve (approved: true) si le score est supérieur à 0.6.

        Répond UNIQUEMENT en JSON valide. Ne fournis aucun texte en dehors de l'objet JSON.
        Le JSON attendu doit contenir exactement ces champs :
        {{
            "score": 0.8,
            "approved": true,
            "critique": "évaluation constructive de la fidélité, pertinence et exactitude",
            "instructions": "suggestions d'amélioration si nécessaire, ou 'Aucune' si satisfaisant"
        }}
        """
        
        try:
            logger.debug("Calling OpenRouter API for audit")
            audit_result = self._ensure_valid_json_response(prompt, prompt)
            
            logger.info("Audit completed: score=%.2f, approved=%s", 
                       audit_result.get("score", 0), 
                       audit_result.get("approved", False))
            
            return audit_result
            
        except (APIConnectionError, APITimeoutError) as e:
            logger.error("API connection error during audit: %s", str(e), exc_info=True)
            raise
        except APIError as e:
            logger.error("API error during audit: %s", str(e), exc_info=True)
            raise
        except ValueError as e:
            logger.error("Failed to parse audit response as valid JSON: %s", str(e), exc_info=True)
            raise
