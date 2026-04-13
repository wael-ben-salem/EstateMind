import os
import json
from openai import OpenAI


client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url="https://tokenfactory.esprit.tn/api",
)


def call_llm_for_decision(state: dict) -> dict:
    prompt = f"""
Tu es un agent IA qui contrôle un pipeline de scraping + ETL immobilier.

Ta mission:
- décider s'il faut lancer le scraping
- décider s'il faut lancer la validation
- décider s'il faut lancer l'ETL
- décider s'il faut générer un rapport

Règles:
- Si raw_exists = false => scrape = true
- Si raw_age_hours > 12 => scrape = true
- Si raw_record_count < 500 => scrape = true
- Si les données semblent correctes => scrape = false, validate = true, etl = true
- report doit toujours être true

Retourne UNIQUEMENT un JSON valide avec cette structure:
{{
  "scrape": true,
  "validate": true,
  "etl": true,
  "report": true,
  "reason": "explication courte",
  "confidence": 0.95
}}

Etat actuel:
{json.dumps(state, indent=2, ensure_ascii=False)}
"""

    response = client.chat.completions.create(
        model="hosted_vllm/Llama-3.1-70B-Instruct",
        messages=[
            {"role": "system", "content": "Tu es un agent IA fiable pour pipeline data. Retourne uniquement du JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=300,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    content = response.choices[0].message.content.strip()
    return json.loads(content)