import os
import json
from openai import OpenAI

class LegalGenerator:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://tokenfactory.esprit.tn/api", 
            api_key=os.getenv("ESPRIT_LLM_API_KEY")
        )
        self.model = "hosted_vllm/Llama-3.1-70B-Instruct"

    def execute_draft(self, query, context, feedback=None, previous_answer=None):
        # 1. SYSTEM PROMPT: Defines the JSON Schema
        system_prompt = """
        Tu es un assistant juridique expert en droit tunisien. 
        Tu dois impérativement répondre au format JSON structuré.
        
        CONSIGNES :
        - Utilise UNIQUEMENT le contexte fourni.
        - Cite les numéros d'articles, les extraits exacts et la source.
        - Si l'information manque, indique-le dans le champ "observations".

        FORMAT JSON REQUIS :
        {
            "resume_contexte": "Résumé concis des points clés du contexte pour cette question",
            "reponse_juridique": "La réponse complète et formelle destinée à l'utilisateur",
            "references": [
                {"article": "N°", "source": "Nom du code/loi", "extrait": "Texte exact cité"}
            ],
            "corrections_apportees": "Si un feedback a été fourni, explique ce qui a été corrigé (sinon vide)",
            "observations": "Notes sur les limites de la réponse ou infos manquantes"
        }
        """

        # 2. USER CONTENT: Logic for Initial vs. Correction
        if not feedback:
            user_content = f"CONTEXTE:\n{context}\n\nQUESTION: {query}"
        else:
            user_content = f"""
            CONTEXTE:
            {context}
            
            TON PRÉCÉDENT ESSAI:
            {previous_answer}
            
            CRITIQUES DE L'AUDITEUR:
            {feedback}
            
            CONSIGNE: Corrige ta réponse pour qu'elle soit parfaitement fidèle au contexte et réponde à toutes les critiques.
 
            """

        # 3. LLM CALL
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            # We force JSON mode here
            response_format={"type": "json_object"},
            temperature=0.1
        )

        # Returns the parsed JSON object
        return json.loads(response.choices[0].message.content)