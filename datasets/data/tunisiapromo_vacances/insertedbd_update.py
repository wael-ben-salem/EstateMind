# script_vacances_quotidien.py
import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime

# CONFIGURATION
URI = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "EstateMind"
COLLECTION_NAME = "tunisiepromo.vacances"
FILE_NAME = "tunisiapromo_vacances_final.json"

print(f"🚀 Mise à jour quotidienne Locations de Vacances - {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 1. Connexion
client = MongoClient(URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# 2. Charger les données
with open(FILE_NAME, 'r', encoding='utf-8') as f:
    data = json.load(f)
    annonces = data['annonces'] if 'annonces' in data else data

print(f"📊 {len(annonces)} locations de vacances dans le fichier")

# 3. Préparer les opérations
operations = []
for annonce in annonces:
    annonce['_derniere_mise_a_jour'] = datetime.now()
    annonce['_site'] = 'tunisiapromo.com'
    operations.append(
        UpdateOne(
            {'annonce_id': annonce.get('annonce_id')},
            {'$set': annonce},
            upsert=True
        )
    )

# 4. Exécuter par lots
total_nouvelles = 0
for i in range(0, len(operations), 50):
    batch = operations[i:i+50]
    resultat = collection.bulk_write(batch)
    total_nouvelles += resultat.upserted_count
    print(f"   Lot {i//50 + 1}: {resultat.upserted_count} nouvelles")

# 5. Résultat
total = collection.count_documents({})
villas = collection.count_documents({"type_bien_normalise": "villa"})
avec_piscine = collection.count_documents({"a_piscine": True})

print(f"\n✅ Total locations vacances: {total}")
print(f"   • Villas: {villas}")
print(f"   • Avec piscine: {avec_piscine}")
print(f"📈 Nouvelles aujourd'hui: {total_nouvelles}")

client.close()