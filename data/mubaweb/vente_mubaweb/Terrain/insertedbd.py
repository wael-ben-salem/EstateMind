"""
SCRIPT D'INSERTION DES DONNÉES TERRAINS DANS MONGODB ATLAS
Base de données: EstateMind
Collection: Mubaweb.vente.Terrain
Fichier: terrain_clean.json (1141 terrains)
"""

import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime
import os

def inserer_vente_terrains():
    print("="*70)
    print("🚀 INSERTION DES DONNÉES TERRAINS DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: EstateMind")
    print("📁 Collection: Mubaweb.vente.Terrain")
    print("📊 Fichier: terrain_clean.json (1141 terrains)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"              # ✅ CHANGÉ
    NOM_COLLECTION = "Mubaweb.vente.Terrain"     # ✅ CHANGÉ
    NOM_FICHIER = "terrain_clean.json"
    
    # 1. Vérifier que le fichier existe
    if not os.path.exists(NOM_FICHIER):
        print(f"❌ ERREUR: Le fichier {NOM_FICHIER} n'existe pas!")
        print(f"📁 Répertoire courant: {os.getcwd()}")
        print("\n📋 Fichiers disponibles dans le répertoire:")
        for fichier in os.listdir('.'):
            if fichier.endswith('.json'):
                print(f"   - {fichier}")
        return
    
    # 2. Charger les données JSON
    print(f"\n📂 Lecture du fichier: {NOM_FICHIER}")
    try:
        with open(NOM_FICHIER, 'r', encoding='utf-8') as fichier:
            donnees = json.load(fichier)
        
        # Afficher les métadonnées
        if 'metadata' in donnees:
            metadata = donnees['metadata']
            print(f"\n📊 MÉTADONNÉES DU FICHIER:")
            print(f"   • Date d'export: {metadata.get('date_export', 'N/A')}")
            print(f"   • Total listings: {metadata.get('total_listings', 0)}")
            print(f"   • Régions: {', '.join(metadata.get('regions', []))}")
            
            if 'scraping_stats' in metadata:
                stats = metadata['scraping_stats']
                print(f"   • Pages scrapées: {stats.get('pages_scraped', 0)}")
                print(f"   • Annonces trouvées: {stats.get('listings_found', 0)}")
        
        # Extraire la liste des terrains
        if isinstance(donnees, dict) and 'listings' in donnees:
            terrains = donnees['listings']
        elif isinstance(donnees, list):
            terrains = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_terrains = len(terrains)
        print(f"\n✅ {nombre_terrains} terrains trouvés dans le fichier")
        
        # Afficher les attributs disponibles
        if nombre_terrains > 0:
            print("\n📋 Attributs disponibles dans les données:")
            attributs = list(terrains[0].keys())
            for i, attr in enumerate(attributs[:20], 1):
                print(f"   {i}. {attr}")
            if len(attributs) > 20:
                print(f"   ... et {len(attributs) - 20} autres attributs")
            
            # Afficher un exemple de terrain
            print("\n🔍 Exemple de terrain (premier du fichier):")
            exemple = terrains[0]
            champs_importants = ['id', 'titre', 'ville', 'surface', 'prix_text', 'type_terrain']
            for champ in champs_importants:
                if champ in exemple:
                    valeur = exemple[champ]
                    if isinstance(valeur, list) and valeur:
                        valeur = ', '.join(str(v) for v in valeur[:3])
                        if len(exemple[champ]) > 3:
                            valeur += f" et {len(exemple[champ]) - 3} autres"
                    print(f"   • {champ}: {valeur}")
        
    except Exception as e:
        print(f"❌ Erreur de lecture: {e}")
        return
    
    # 3. Connexion à MongoDB Atlas
    print(f"\n🔌 Connexion à MongoDB Atlas...")
    try:
        client = MongoClient(CHAINE_CONNEXION)
        client.admin.command('ping')
        print("✅ Connexion réussie!")
        
        # Sélectionner la base "EstateMind" et la collection "Mubaweb.vente.Terrain"
        db = client[NOM_BASE_DONNEES]
        collection = db[NOM_COLLECTION]
        
        print(f"✅ Base de données '{NOM_BASE_DONNEES}' sélectionnée")
        print(f"✅ Collection '{NOM_COLLECTION}' sélectionnée")
        
        # Vérifier si la collection existe déjà
        collections = db.list_collection_names()
        if NOM_COLLECTION in collections:
            ancien_nombre = collection.count_documents({})
            print(f"📊 La collection '{NOM_COLLECTION}' existe déjà avec {ancien_nombre} documents")
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n💡 Vérifiez que:")
        print("   - Votre chaîne de connexion est correcte")
        print("   - Votre IP est autorisée dans MongoDB Atlas")
        return
    
    # 4. Préparer les documents
    print("\n🔄 Préparation des documents...")
    documents = []
    erreurs = []
    
    for i, terrain in enumerate(terrains):
        try:
            doc = terrain.copy()
            
            # Métadonnées
            doc['_date_insertion'] = datetime.now()
            doc['_type_collection'] = 'vente_terrains'
            
            if 'id' not in doc:
                doc['id'] = str(i + 1)
            
            if 'surface' in doc and doc['surface'] is not None:
                try:
                    doc['surface'] = float(doc['surface'])
                except:
                    pass
            
            if 'prix' in doc and doc['prix'] is not None:
                try:
                    doc['prix'] = float(doc['prix'])
                except:
                    pass
            
            for champ in ['types_terrain', 'vocations', 'situations_juridiques',
                         'viabilisation', 'constructibilite', 'proximites']:
                if champ in doc and doc[champ] == []:
                    doc[champ] = []
            
            documents.append(doc)
            
        except Exception as e:
            erreurs.append((i, str(e)))
    
    if erreurs:
        print(f"⚠️ {len(erreurs)} terrains ont eu des erreurs lors de la préparation")
        for err in erreurs[:5]:
            print(f"   • Terrain {err[0]}: {err[1]}")
    
    print(f"✅ {len(documents)} terrains prêts à être insérés sur {nombre_terrains}")
    
    # 5. VIDER LA COLLECTION
    print(f"\n🗑️ Nettoyage de la collection {NOM_COLLECTION}...")
    try:
        resultat_suppression = collection.delete_many({})
        print(f"✅ {resultat_suppression.deleted_count} anciens documents supprimés")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    # 6. CRÉER DES INDEX
    print("\n🔧 Création des index...")
    try:
        collection.create_index("id", unique=False)
        print("✅ Index créé sur le champ 'id'")
        
        collection.create_index("ville")
        print("✅ Index créé sur le champ 'ville'")
        
        collection.create_index("region")
        print("✅ Index créé sur le champ 'region'")
        
        collection.create_index("surface")
        print("✅ Index créé sur le champ 'surface'")
        
        collection.create_index("type_terrain")
        print("✅ Index créé sur le champ 'type_terrain'")
        
        collection.create_index("types_terrain")
        print("✅ Index créé sur le champ 'types_terrain'")
        
        if 'localisation.coordinates' in terrains[0]:
            collection.create_index([("localisation.coordinates", "2dsphere")])
            print("✅ Index géospatial créé")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 7. INSÉRER TOUS LES DOCUMENTS
    print(f"\n💾 Insertion de {len(documents)} terrains dans {NOM_COLLECTION}...")
    
    try:
        total_insere = 0
        taille_lot = 100
        
        for i in range(0, len(documents), taille_lot):
            lot = documents[i:i+taille_lot]
            try:
                resultat_lot = collection.insert_many(lot, ordered=False)
                total_insere += len(resultat_lot.inserted_ids)
                print(f"   ✅ Lot {i//taille_lot + 1}: {len(resultat_lot.inserted_ids)} terrains insérés")
            except Exception as e_lot:
                print(f"   ⚠️ Lot {i//taille_lot + 1}: Erreur - insertion individuelle...")
                for doc in lot:
                    try:
                        collection.insert_one(doc)
                        total_insere += 1
                    except Exception as e_doc:
                        print(f"      ✗ Terrain {doc.get('id', 'inconnu')} non inséré: {str(e_doc)[:50]}")
        
        print(f"\n✅ Total inséré: {total_insere}/{len(documents)} terrains")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion: {e}")
    
    # 8. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre de terrains dans {NOM_COLLECTION}: {nombre_final}")
    
    if nombre_final == len(documents):
        print("✅ SUCCÈS TOTAL: Tous les terrains sont présents!")
    elif nombre_final > 0:
        pourcentage = (nombre_final / len(documents)) * 100
        print(f"⚠️ Partiel: {nombre_final}/{len(documents)} terrains présents ({pourcentage:.1f}%)")
    else:
        print("❌ Aucun terrain n'a été inséré")
    
    # 9. Échantillon
    if nombre_final > 0:
        print("\n🔍 Échantillon des terrains insérés:")
        terrains_exemples = collection.find().limit(3)
        for i, terrain in enumerate(terrains_exemples, 1):
            print(f"\n   📍 Terrain {i}:")
            print(f"      • ID: {terrain.get('id', 'N/A')}")
            print(f"      • Titre: {terrain.get('titre', 'N/A')[:50]}...")
            print(f"      • Ville: {terrain.get('ville', 'N/A')}")
            print(f"      • Surface: {terrain.get('surface', 'N/A')} m²")
            print(f"      • Prix: {terrain.get('prix_text', 'N/A')}")
            if 'types_terrain' in terrain and terrain['types_terrain']:
                print(f"      • Type: {', '.join(terrain['types_terrain'][:2])}")
    
    # 10. Statistiques
    print("\n" + "="*70)
    print("📊 STATISTIQUES DES TERRAINS")
    print("="*70)
    
    try:
        print("\n📍 Par région:")
        regions = collection.aggregate([
            {"$group": {"_id": "$region", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for r in regions:
            if r['_id']:
                print(f"   • {r['_id']}: {r['count']} terrains")
        
        print("\n🏙️ Top 10 villes:")
        villes = collection.aggregate([
            {"$group": {"_id": "$ville", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])
        for v in villes:
            if v['_id']:
                print(f"   • {v['_id']}: {v['count']} terrains")
        
        print("\n🏷️ Types de terrain:")
        types = collection.aggregate([
            {"$unwind": {"path": "$types_terrain", "preserveNullAndEmptyArrays": False}},
            {"$group": {"_id": "$types_terrain", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ])
        for t in types:
            if t['_id']:
                print(f"   • {t['_id']}: {t['count']} terrains")
        
        stats_surface = collection.aggregate([
            {"$match": {"surface": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$surface"},
                "max": {"$max": "$surface"},
                "moyen": {"$avg": "$surface"},
                "total": {"$sum": 1}
            }}
        ])
        for s in stats_surface:
            print(f"\n📐 Surfaces:")
            print(f"   • Min: {s['min']:,.0f} m²")
            print(f"   • Max: {s['max']:,.0f} m²")
            print(f"   • Moyenne: {s['moyen']:,.0f} m²")
            print(f"   • Terrains avec surface: {s['total']}")
        
        print("\n🎯 Vocations:")
        vocations = collection.aggregate([
            {"$unwind": {"path": "$vocations", "preserveNullAndEmptyArrays": False}},
            {"$group": {"_id": "$vocations", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ])
        for v in vocations:
            if v['_id']:
                print(f"   • {v['_id']}: {v['count']} terrains")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du calcul des statistiques: {e}")
    
    # 11. Récapitulatif de toutes les collections (dans EstateMind)
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF BASE DE DONNÉES EstateMind")
    print("="*70)
    
    try:
        collections_info = {}
        for nom_collection in db.list_collection_names():
            count = db[nom_collection].count_documents({})
            collections_info[nom_collection] = count
        
        for nom, count in collections_info.items():
            print(f"📍 Collection '{nom}': {count} documents")
        
        total_documents = sum(collections_info.values())
        print(f"\n📌 TOTAL GÉNÉRAL: {total_documents} documents dans la base EstateMind")
        
        # Vérification spéciale pour la collection demandée
        if NOM_COLLECTION in collections_info:
            if collections_info[NOM_COLLECTION] == 1141:
                print("✅ Les 1141 terrains ont bien été insérés!")
            else:
                print(f"⚠️ Attention: {collections_info[NOM_COLLECTION]}/1141 terrains insérés")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du récapitulatif: {e}")
    
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ Vérifie sur MongoDB Atlas:")
    print("   Collections → EstateMind → Mubaweb.vente.Terrain")

if __name__ == "__main__":
    inserer_vente_terrains()
