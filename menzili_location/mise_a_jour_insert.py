# script_menzili_locations_quotidien.py
import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime

# CONFIGURATION
URI = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "EstateMind"
COLLECTION_NAME = "menzili.location"
FILE_NAME = "menzili_location_final.json"

print(f"🚀 Mise à jour quotidienne Menzili Locations - {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 1. Connexion
client = MongoClient(URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# 2. Charger les nouvelles données
with open(FILE_NAME, 'r', encoding='utf-8') as f:
    data = json.load(f)
    annonces = data['annonces'] if 'annonces' in data else data

print(f"📊 {len(annonces)} locations dans le fichier")

# 3. Ajouter le type d'offre et préparer les opérations
operations = []
for annonce in annonces:
    annonce['type_offre'] = 'Location'
    annonce['_derniere_mise_a_jour'] = datetime.now()
    operations.append(
        UpdateOne(
            {'annonce_id': annonce.get('annonce_id')},
            {'$set': annonce},
            upsert=True
        )
    )

# 4. Exécuter par lots
total_nouvelles = 0
for i in range(0, len(operations), 1000):
    batch = operations[i:i+1000]
    resultat = collection.bulk_write(batch)
    total_nouvelles += resultat.upserted_count
    print(f"   Lot {i//1000 + 1}: {resultat.upserted_count} nouvelles locations")

# 5. Résultat
total_ventes = collection.count_documents({"type_offre": "Vente"})
total_locations = collection.count_documents({"type_offre": "Location"})
print(f"\n✅ Total locations dans la base: {total_locations}")
print(f"✅ Total ventes dans la base: {total_ventes}")
print(f"📈 TOTAL GÉNÉRAL: {total_ventes + total_locations} annonces")
print(f"📈 Nouvelles locations aujourd'hui: {total_nouvelles}")

client.close()