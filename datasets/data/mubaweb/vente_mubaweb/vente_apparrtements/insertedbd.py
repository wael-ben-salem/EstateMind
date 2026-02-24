"""
SCRIPT D'INSERTION DES DONNÉES APPARTEMENTS DANS MONGODB ATLAS
Base de données: EstateMind
Collection: Mubaweb.vente.Appartements
Fichier: appartements_final.json (3222 appartements)
"""

import json
from pymongo import MongoClient
from datetime import datetime
import os
import time

def inserer_vente_appartements():
    print("="*70)
    print("🚀 INSERTION DES DONNÉES APPARTEMENTS DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: EstateMind")
    print("📁 Collection: Mubaweb.vente.Appartements")
    print("📊 Fichier: appartements_final.json (3222 appartements)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"                 # ✅ CHANGÉ
    NOM_COLLECTION = "Mubaweb.vente.Appartements"   # ✅ CHANGÉ
    NOM_FICHIER = "appartements_final.json"
    
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
            print(f"   • Régions: {', '.join(metadata.get('regions', [])[:5])}...")
            
            if 'scraping_stats' in metadata:
                stats = metadata['scraping_stats']
                print(f"   • Pages scrapées: {stats.get('pages_scraped', 0)}")
                print(f"   • Annonces trouvées: {stats.get('listings_found', 0)}")
            
            if 'regions_stats' in metadata:
                print("\n   📍 Statistiques par région:")
                regions_stats = metadata['regions_stats']
                for region, stats in list(regions_stats.items())[:5]:
                    print(f"      • {region}: {stats.get('annonces_scrapees', 0)} annonces")
        
        if 'validation_warnings' in donnees.get('metadata', {}):
            warnings = donnees['metadata']['validation_warnings']
            print(f"\n⚠️ {len(warnings)} avertissements de validation (incohérences de prix)")
        
        # Extraire la liste des appartements
        if isinstance(donnees, dict) and 'listings' in donnees:
            appartements = donnees['listings']
        elif isinstance(donnees, list):
            appartements = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_appartements = len(appartements)
        print(f"\n✅ {nombre_appartements} appartements trouvés dans le fichier")
        
        if nombre_appartements == 3222:
            print("✅ Nombre d'appartements conforme aux métadonnées (3222)")
        else:
            print(f"⚠️ Attention: {nombre_appartements} trouvés, mais les métadonnées indiquent 3222")
        
        if nombre_appartements > 0:
            print("\n📋 Attributs disponibles dans les données:")
            attributs = list(appartements[0].keys())
            for i, attr in enumerate(attributs[:20], 1):
                print(f"   {i}. {attr}")
            if len(attributs) > 20:
                print(f"   ... et {len(attributs) - 20} autres attributs")
            
            print("\n🔍 Exemple d'appartement (premier du fichier):")
            exemple = appartements[0]
            champs_importants = ['id', 'titre', 'ville', 'quartier', 'surface', 'prix_text', 'type_appartement', 'nombre_pieces']
            for champ in champs_importants:
                if champ in exemple and exemple[champ]:
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
        
        db = client[NOM_BASE_DONNEES]
        collection = db[NOM_COLLECTION]
        
        print(f"✅ Base de données '{NOM_BASE_DONNEES}' sélectionnée")
        print(f"✅ Collection '{NOM_COLLECTION}' sélectionnée")
        
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
    
    for i, appartement in enumerate(appartements):
        try:
            doc = appartement.copy()
            doc['_date_insertion'] = datetime.now()
            doc['_type_collection'] = 'vente_appartements'
            
            if 'id' not in doc:
                doc['id'] = str(i + 1)
            
            if 'surface' in doc and doc['surface'] is not None:
                try: doc['surface'] = float(doc['surface'])
                except: pass
            
            if 'prix' in doc and doc['prix'] is not None:
                try: doc['prix'] = float(doc['prix'])
                except: pass
            
            if 'prix_m2' in doc and doc['prix_m2'] is not None:
                try: doc['prix_m2'] = float(doc['prix_m2'])
                except: pass
            
            if 'nombre_pieces' in doc and doc['nombre_pieces'] is not None:
                try: doc['nombre_pieces'] = int(doc['nombre_pieces'])
                except: pass
            
            if 'nombre_chambres' in doc and doc['nombre_chambres'] is not None:
                try: doc['nombre_chambres'] = int(doc['nombre_chambres'])
                except: pass
            
            documents.append(doc)
            
        except Exception as e:
            erreurs.append((i, str(e)))
    
    if erreurs:
        print(f"⚠️ {len(erreurs)} appartements ont eu des erreurs lors de la préparation")
        for err in erreurs[:5]:
            print(f"   • Appartement {err[0]}: {err[1]}")
    
    print(f"✅ {len(documents)} appartements prêts à être insérés sur {nombre_appartements}")
    
    # 5. VIDER LA COLLECTION
    print(f"\n🗑️ Nettoyage de la collection {NOM_COLLECTION}...")
    try:
        resultat_suppression = collection.delete_many({})
        print(f"✅ {resultat_suppression.deleted_count} anciens documents supprimés")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    # 6. INDEX
    print("\n🔧 Création des index...")
    try:
        collection.create_index("id", unique=False); print("✅ Index: id")
        collection.create_index("ville"); print("✅ Index: ville")
        collection.create_index("region"); print("✅ Index: region")
        collection.create_index("quartier"); print("✅ Index: quartier")
        collection.create_index("prix"); print("✅ Index: prix")
        collection.create_index("surface"); print("✅ Index: surface")
        collection.create_index("type_appartement"); print("✅ Index: type_appartement")
        collection.create_index("nombre_pieces"); print("✅ Index: nombre_pieces")
        collection.create_index("nombre_chambres"); print("✅ Index: nombre_chambres")
        collection.create_index("nom_agence"); print("✅ Index: nom_agence")
        
        if 'localisation' in appartements[0] and 'coordinates' in appartements[0].get('localisation', {}):
            collection.create_index([("localisation.coordinates", "2dsphere")])
            print("✅ Index géospatial créé")
        
        collection.create_index([("ville", 1), ("prix", -1)])
        print("✅ Index composé créé (ville + prix)")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 7. INSÉRER
    print(f"\n💾 Insertion de {len(documents)} appartements dans {NOM_COLLECTION}...")
    print("   Insertion par lots de 100 documents...")
    
    try:
        total_insere = 0
        taille_lot = 100
        debut = time.time()
        
        for i in range(0, len(documents), taille_lot):
            lot = documents[i:i+taille_lot]
            try:
                resultat_lot = collection.insert_many(lot, ordered=False)
                total_insere += len(resultat_lot.inserted_ids)
                pourcentage = (total_insere / len(documents)) * 100
                print(f"   ✅ Lot {i//taille_lot + 1}: {len(resultat_lot.inserted_ids)} insérés ({pourcentage:.1f}%)")
            except Exception:
                print(f"   ⚠️ Lot {i//taille_lot + 1}: insertion individuelle...")
                for doc in lot:
                    try:
                        collection.insert_one(doc)
                        total_insere += 1
                    except Exception as e_doc:
                        print(f"      ✗ Appartement {doc.get('id', 'inconnu')} non inséré: {str(e_doc)[:50]}")
        
        duree = time.time() - debut
        print(f"\n✅ Total inséré: {total_insere}/{len(documents)} appartements en {duree:.1f} secondes")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion: {e}")
    
    # 8. Vérification
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre d'appartements dans {NOM_COLLECTION}: {nombre_final}")
    
    if nombre_final == len(documents):
        print("✅ SUCCÈS TOTAL: Tous les appartements sont présents!")
    elif nombre_final > 0:
        pourcentage = (nombre_final / len(documents)) * 100
        print(f"⚠️ Partiel: {nombre_final}/{len(documents)} présents ({pourcentage:.1f}%)")
    else:
        print("❌ Aucun appartement n'a été inséré")
    
    # 9. Échantillon
    if nombre_final > 0:
        print("\n🔍 Échantillon des appartements insérés:")
        appartements_exemples = collection.find().limit(3)
        for i, app in enumerate(appartements_exemples, 1):
            print(f"\n   🏢 Appartement {i}:")
            print(f"      • ID: {app.get('id', 'N/A')}")
            print(f"      • Titre: {app.get('titre', 'N/A')[:60]}...")
            print(f"      • Ville: {app.get('ville', 'N/A')}")
            print(f"      • Quartier: {app.get('quartier', 'N/A')}")
            print(f"      • Surface: {app.get('surface', 'N/A')} m²")
            print(f"      • Prix: {app.get('prix_text', 'N/A')}")
            print(f"      • Type: {app.get('type_appartement', 'N/A')}")
            print(f"      • Pièces: {app.get('nombre_pieces', 'N/A')}")
    
    # 10. Récapitulatif (EstateMind + nouveaux noms)
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF BASE DE DONNÉES EstateMind")
    print("="*70)
    
    try:
        collections_info = {c: db[c].count_documents({}) for c in db.list_collection_names()}
        
        ordre = [
            "Mubaweb.vente.Appartements",
            "Mubaweb.vente.Terrain",
            "Mubaweb.locationNeuf",
            "Mubaweb.locations_vacances",
        ]
        
        for nom in ordre:
            if nom in collections_info:
                print(f"📍 Collection '{nom}': {collections_info[nom]} documents")
        
        for nom, count in collections_info.items():
            if nom not in ordre:
                print(f"📍 Collection '{nom}': {count} documents")
        
        total_documents = sum(collections_info.values())
        print(f"\n📌 TOTAL GÉNÉRAL: {total_documents} documents dans la base EstateMind")
        
        if NOM_COLLECTION in collections_info:
            if collections_info[NOM_COLLECTION] == 3222:
                print("✅ Les 3222 appartements ont bien été insérés!")
            else:
                print(f"⚠️ Attention: {collections_info[NOM_COLLECTION]}/3222 appartements insérés")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du récapitulatif: {e}")
    
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ Vérifie sur MongoDB Atlas:")
    print("   Collections → EstateMind → Mubaweb.vente.Appartements")

if __name__ == "__main__":
    inserer_vente_appartements()
