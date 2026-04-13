import os
import json
from openai import OpenAI

INPUT_FILE = "/opt/spark_app/data/TayaraDataRegex.json"
OUTPUT_FILE = "/opt/spark_app/data/TayaraDataEnriched.json"

client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url="https://tokenfactory.esprit.tn/api",
)

def llm_extract(item):
    title = item.get("title", "") or ""
    description = item.get("description", "") or ""
    location = item.get("location", "") or ""

    prompt = f"""
Tu es un extracteur immobilier tunisien.

Complète uniquement les champs manquants ou ambigus.
N'invente rien.
Retourne UNIQUEMENT un JSON valide avec cette structure :

{{
  "num_etage": null,
  "adresse_raw": null,
  "ville": null,
  "quartier": null,
  "delegation": null,
  "gouvernorat": null,
  "surface_extraite": null,
  "nb_chambres_extrait": null,
  "nb_sdb_extrait": null,
  "type_bien_extrait": null,
  "usage_extrait": null,
  "transaction_type_extrait": null,
  "titre_foncier_extrait": null,
  "extraction_confidence": 0.0
}}

Titre:
{title}

Location:
{location}

Description:
{description}
"""

    response = client.chat.completions.create(
        model="hosted_vllm/Llama-3.1-70B-Instruct",
        messages=[
            {"role": "system", "content": "Tu es un extracteur JSON strict. Réponds uniquement avec du JSON valide."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=350,
        top_p=0.9,
    )

    return json.loads(response.choices[0].message.content.strip())

def merge_values(original, extracted):
    merged = original.copy()
    for key, value in extracted.items():
        if merged.get(key) in [None, "", []] and value not in [None, "", []]:
            merged[key] = value

    merged["source_extraction"] = "regex+llm"
    merged["extraction_confidence"] = max(
        float(merged.get("extraction_confidence") or 0),
        float(extracted.get("extraction_confidence") or 0)
    )
    merged["needs_llm_enrichment"] = False
    return merged

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []

    for i, item in enumerate(data, start=1):
        if item.get("needs_llm_enrichment") is True:
            try:
                extracted = llm_extract(item)
                item = merge_values(item, extracted)
            except Exception as e:
                print(f"[LLM ERROR] row {i}: {e}")
        result.append(item)

        if i % 50 == 0:
            print(f"Processed {i} rows")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"LLM fallback enrichment saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()