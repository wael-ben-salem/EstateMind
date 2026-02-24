"""
SCRIPT D'INSERTION DES DONNÉES LOCAUX COMMERCIAUX DANS MONGODB ATLAS
Base de données: EstateMind
Collection: Mubaweb.vente.LocauxCommerciaux
Fichier: locaux_final.json (121 locaux commerciaux)
"""

import json
from pymongo import MongoClient
from datetime import datetime
import os
import time

def inserer_vente_locaux_commerciaux():
    print("="*70)
    print("🚀 INSERTION DES DONNÉES LOCAUX COMMERCIAUX DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: EstateMind")
    print("📁 Collection: Mubaweb.vente.LocauxCommerciaux")
    print("📊 Fichier: locaux_final.json (121 locaux commerciaux)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"                     # ✅ CHANGÉ
    NOM_COLLECTION = "Mubaweb.vente.LocauxCommerciaux"  # ✅ CHANGÉ
    NOM_FICHIER = "locaux_final.json"
    
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
            print(f"   • Type de bien: {metadata.get('property_type', 'N/A')}")
            print(f"   • Régions: {', '.join(metadata.get('regions', []))}")
            
            if 'scraping_stats' in metadata:
                stats = metadata['scraping_stats']
                print(f"   • Pages scrapées: {stats.get('pages_scraped', 0)}")
                print(f"   • Annonces trouvées: {stats.get('listings_found', 0)}")
            
            if 'statistiques_extraction' in metadata:
                stats_extract = metadata['statistiques_extraction']
                print(f"\n   📊 Statistiques d'extraction:")
                print(f"      • Prix extraits: {stats_extract.get('prix_extraits', 0)}")
                print(f"      • Mezzanines détectées: {stats_extract.get('mezzanines_detectees', 0)}")
                print(f"      • Double hauteur: {stats_extract.get('double_hauteur_detectees', 0)}")
                print(f"      • Catalogues trouvés: {stats_extract.get('catalogues_trouves', 0)}")
        
        # Extraire la liste des locaux commerciaux
        if isinstance(donnees, dict) and 'listings' in donnees:
            locaux = donnees['listings']
        elif isinstance(donnees, list):
            locaux = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_locaux = len(locaux)
        print(f"\n✅ {nombre_locaux} locaux commerciaux trouvés dans le fichier")
        
        if nombre_locaux == 121:
            print("✅ Nombre de locaux conforme aux métadonnées (121)")
        else:
            print(f"⚠️ Attention: {nombre_locaux} trouvés, mais les métadonnées indiquent 121")
        
        if nombre_locaux > 0:
            print("\n📋 Attributs spécifiques aux locaux commerciaux:")
            attributs_specifiques = [
                'type_local', 'surface', 'surface_mezzanine', 'a_mezzanine',
                'double_hauteur', 'nombre_vitrines', 'parking_nombre',
                'a_alarme', 'zone_activite', 'amenities_commercial'
            ]
            for attr in attributs_specifiques:
                if attr in locaux[0]:
                    print(f"   • {attr}")
            
            print("\n🔍 Exemple de local commercial (premier du fichier):")
            exemple = locaux[0]
            champs_importants = [
                'id', 'titre', 'type_local', 'ville', 'quartier', 'surface',
                'prix_text', 'a_mezzanine', 'double_hauteur', 'nombre_sdb'
            ]
            for champ in champs_importants:
                if champ in exemple and exemple[champ] is not None:
                    valeur = exemple[champ]
                    if isinstance(valeur, bool):
                        valeur = "Oui" if valeur else "Non"
                    elif isinstance(valeur, float) and champ == 'surface':
                        valeur = f"{valeur} m²"
                    print(f"   • {champ}: {valeur}")
            
            if 'equipements' in exemple and exemple['equipements']:
                print(f"   • équipements: {', '.join(exemple['equipements'][:5])}...")
            
    except Exception as e:
        print(f"❌ Erreur de lecture: {e}")
        return
    
    # 3. Connexion à MongoDB Atlas
    print(f"\n🔌 Connexion à MongoDB Atlas...")
    try:
        client = MongoClient(CHAINE_CONNEXION)
        client.admin.command('ping')
        print("✅ Connexion réussie!")
        
        # Sélectionner la base "EstateMind" et la collection "Mubaweb.vente.LocauxCommerciaux"
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
    
    for i, local in enumerate(locaux):
        try:
            doc = local.copy()
            doc['_date_insertion'] = datetime.now()
            doc['_type_collection'] = 'vente_locaux_commerciaux'
            
            if 'id' not in doc:
                doc['id'] = str(i + 1)
            
            if 'surface' in doc and doc['surface'] is not None:
                try: doc['surface'] = float(doc['surface'])
                except: pass
            
            if 'surface_mezzanine' in doc and doc['surface_mezzanine'] is not None:
                try: doc['surface_mezzanine'] = float(doc['surface_mezzanine'])
                except: pass
            
            if 'prix' in doc and doc['prix'] is not None:
                try: doc['prix'] = float(doc['prix'])
                except: pass
            
            if 'prix_m2' in doc and doc['prix_m2'] is not None:
                try: doc['prix_m2'] = float(doc['prix_m2'])
                except: pass
            
            for champ_bool in [
                'a_mezzanine', 'double_hauteur', 'a_terrasse', 'acces_livraison',
                'possibilite_enseigne', 'a_alarme', 'a_monte_charge', 'accessibilite_pmr'
            ]:
                if champ_bool in doc and doc[champ_bool] is not None and isinstance(doc[champ_bool], str):
                    doc[champ_bool] = doc[champ_bool].lower() == 'true'
            
            documents.append(doc)
            
        except Exception as e:
            erreurs.append((i, str(e)))
    
    if erreurs:
        print(f"⚠️ {len(erreurs)} locaux ont eu des erreurs lors de la préparation")
        for err in erreurs[:5]:
            print(f"   • Local {err[0]}: {err[1]}")
    
    print(f"✅ {len(documents)} locaux commerciaux prêts à être insérés sur {nombre_locaux}")
    
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
        collection.create_index("type_local"); print("✅ Index: type_local")
        collection.create_index("ville"); print("✅ Index: ville")
        collection.create_index("quartier"); print("✅ Index: quartier")
        collection.create_index("prix"); print("✅ Index: prix")
        collection.create_index("surface"); print("✅ Index: surface")
        collection.create_index("a_mezzanine"); print("✅ Index: a_mezzanine")
        collection.create_index("double_hauteur"); print("✅ Index: double_hauteur")
        
        if 'localisation' in locaux[0] and 'coordinates' in locaux[0].get('localisation', {}):
            collection.create_index([("localisation.coordinates", "2dsphere")])
            print("✅ Index géospatial créé")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 7. INSÉRER (121 locaux)
    print(f"\n💾 Insertion de {len(documents)} locaux commerciaux dans {NOM_COLLECTION}...")
    
    try:
        debut = time.time()
        resultat = collection.insert_many(documents, ordered=False)
        duree = time.time() - debut
        print(f"\n✅ {len(resultat.inserted_ids)} locaux commerciaux insérés en {duree:.1f} secondes")
        
    except Exception as e:
        print(f"\n⚠️ Erreur lors de l'insertion massive: {e}")
        print("\n🔄 Tentative d'insertion par lots...")
        
        try:
            total_insere = 0
            taille_lot = 20
            
            for i in range(0, len(documents), taille_lot):
                lot = documents[i:i+taille_lot]
                try:
                    resultat_lot = collection.insert_many(lot, ordered=False)
                    total_insere += len(resultat_lot.inserted_ids)
                    print(f"   ✅ Lot {i//taille_lot + 1}: {len(resultat_lot.inserted_ids)} locaux insérés")
                except Exception:
                    print(f"   ⚠️ Lot {i//taille_lot + 1}: Insertion individuelle...")
                    for doc in lot:
                        try:
                            collection.insert_one(doc)
                            total_insere += 1
                            print(f"      ✓ Local {doc.get('id', 'inconnu')} inséré")
                        except Exception as e_doc:
                            print(f"      ✗ Erreur: {e_doc}")
            
            print(f"\n✅ Total inséré: {total_insere}/{len(documents)} locaux")
            
        except Exception as e2:
            print(f"❌ Échec de l'insertion: {e2}")
    
    # 8. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre de locaux dans {NOM_COLLECTION}: {nombre_final}")
    
    if nombre_final == len(documents):
        print("✅ SUCCÈS TOTAL: Tous les locaux commerciaux sont présents!")
    elif nombre_final > 0:
        pourcentage = (nombre_final / len(documents)) * 100
        print(f"⚠️ Partiel: {nombre_final}/{len(documents)} locaux présents ({pourcentage:.1f}%)")
    else:
        print("❌ Aucun local n'a été inséré")
    
    # 9. Échantillon
    if nombre_final > 0:
        print("\n🔍 Échantillon des locaux commerciaux insérés:")
        locaux_exemples = collection.find().limit(3)
        for i, local in enumerate(locaux_exemples, 1):
            print(f"\n   🏢 Local commercial {i}:")
            print(f"      • ID: {local.get('id', 'N/A')}")
            print(f"      • Type: {local.get('type_local', 'N/A')}")
            print(f"      • Titre: {local.get('titre', 'N/A')[:60]}...")
            print(f"      • Ville: {local.get('ville', 'N/A')}")
            print(f"      • Quartier: {local.get('quartier', 'N/A')}")
            print(f"      • Surface: {local.get('surface', 'N/A')} m²")
            if local.get('surface_mezzanine'):
                print(f"      • Mezzanine: {local.get('surface_mezzanine')} m²")
            print(f"      • Prix: {local.get('prix_text', 'N/A')}")
            print(f"      • Mezzanine: {'Oui' if local.get('a_mezzanine') else 'Non'}")
            print(f"      • Double hauteur: {'Oui' if local.get('double_hauteur') else 'Non'}")
    
    # 10. Récapitulatif (EstateMind)
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF BASE DE DONNÉES EstateMind")
    print("="*70)
    
    try:
        collections_info = {c: db[c].count_documents({}) for c in db.list_collection_names()}
        
        ordre = [
            "Mubaweb.vente.Appartements",
            "Mubaweb.vente.Terrain",
            "Mubaweb.vente.LocauxCommerciaux",
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
            if collections_info[NOM_COLLECTION] == 121:
                print("✅ Les 121 locaux commerciaux ont bien été insérés!")
            else:
                print(f"⚠️ Attention: {collections_info[NOM_COLLECTION]}/121 locaux insérés")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du récapitulatif: {e}")
    
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ Vérifie sur MongoDB Atlas:")
    print("   Collections → EstateMind → Mubaweb.vente.LocauxCommerciaux")

if __name__ == "__main__":
    inserer_vente_locaux_commerciaux()
