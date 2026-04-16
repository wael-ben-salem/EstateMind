# script_menzili_quotidien.py
import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime
import os

# CONFIGURATION
URI = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "EstateMind"
COLLECTION_NAME = "menzili.vente"
FILE_NAME = "menzili_final.json"

print(f"🚀 Mise à jour quotidienne Menzili - {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 1. Connexion
client = MongoClient(URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# 2. Créer index unique si nécessaire
collection.create_index("annonce_id", unique=True)

# 3. Charger les nouvelles données
with open(FILE_NAME, 'r', encoding='utf-8') as f:
    data = json.load(f)
    annonces = data['annonces'] if 'annonces' in data else data

print(f"📊 {len(annonces)} annonces dans le fichier")

# 4. Préparer les opérations upsert
operations = []
for annonce in annonces:
    annonce['_derniere_mise_a_jour'] = datetime.now()
    operations.append(
        UpdateOne(
            {'annonce_id': annonce.get('annonce_id')},
            {'$set': annonce},
            upsert=True
        )
    )

# 5. Exécuter par lots
total_nouvelles = 0
for i in range(0, len(operations), 1000):
    batch = operations[i:i+1000]
    resultat = collection.bulk_write(batch)
    total_nouvelles += resultat.upserted_count
    print(f"   Lot {i//1000 + 1}: {resultat.upserted_count} nouvelles")

# 6. Résultat
total = collection.count_documents({})
print(f"✅ Total annonces dans la base: {total}")
print(f"📈 Nouvelles annonces aujourd'hui: {total_nouvelles}")

client.close()