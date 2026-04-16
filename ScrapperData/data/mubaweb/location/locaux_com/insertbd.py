"""
SCRIPT D'INSERTION DES DONNÉES LOCATION LOCAUX COMMERCIAUX DANS MONGODB ATLAS
Base de données: EstateMind
Collection: Mubaweb.location.LocauxCommerciaux
Fichier: locaux_location_final.json (159 locaux commerciaux à louer)
"""

import json
from pymongo import MongoClient
from datetime import datetime
import os
import time

def inserer_location_locaux_commerciaux():
    print("="*70)
    print("🚀 INSERTION DES DONNÉES LOCATION LOCAUX COMMERCIAUX DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: EstateMind")
    print("📁 Collection: Mubaweb.location.LocauxCommerciaux")
    print("📊 Fichier: locaux_location_final.json (159 locaux commerciaux à louer)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"                      # ✅ CHANGÉ
    NOM_COLLECTION  = "Mubaweb.location.LocauxCommerciaux"  # ✅ CHANGÉ
    NOM_FICHIER     = "location_locaux_clean.json"
    
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
                print(f"\n   📍 Statistiques par région:")
                for region, stats_region in stats.get('regions_stats', {}).items():
                    print(f"      • {region}: {stats_region.get('annonces_scrapees', 0)} locaux")
        
        # Extraire la liste des locaux
        if isinstance(donnees, dict) and 'listings' in donnees:
            locaux = donnees['listings']
        elif isinstance(donnees, list):
            locaux = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_locaux = len(locaux)
        print(f"\n✅ {nombre_locaux} locaux commerciaux à louer trouvés dans le fichier")
        
        if nombre_locaux == 159:
            print("✅ Nombre de locaux conforme aux métadonnées (159)")
        else:
            print(f"⚠️ Attention: {nombre_locaux} trouvés, mais les métadonnées indiquent 159")
            
    except Exception as e:
        print(f"❌ Erreur de lecture: {e}")
        return
    
    # 3. Connexion à MongoDB Atlas
    print(f"\n🔌 Connexion à MongoDB Atlas...")
    try:
        client = MongoClient(CHAINE_CONNEXION)
        client.admin.command('ping')
        print("✅ Connexion réussie!")
        
        # ✅ Base: EstateMind | Collection: Mubaweb.location.LocauxCommerciaux
        db = client[NOM_BASE_DONNEES]
        collection = db[NOM_COLLECTION]
        
        print(f"✅ Base de données '{NOM_BASE_DONNEES}' sélectionnée")
        print(f"✅ Collection '{NOM_COLLECTION}' sélectionnée")
        
        if NOM_COLLECTION in db.list_collection_names():
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
            doc['_type_collection'] = 'location_locaux_commerciaux'
            
            if 'id' not in doc:
                doc['id'] = str(i + 1)
            
            # conversions
            for champ_float in ['surface', 'surface_terrasse', 'surface_mezzanine', 'loyer', 'loyer_m2']:
                if champ_float in doc and doc[champ_float] is not None:
                    try:
                        doc[champ_float] = float(doc[champ_float])
                    except:
                        pass
            
            for champ_bool in [
                'est_gerance_libre','a_vitrine','a_mezzanine','a_terrasse','a_parking',
                'parking_clientele','a_livraison','a_enseigne','a_hotte','a_extraction',
                'a_reserve','acces_independant','acces_24h','a_climatisation','a_chauffage',
                'a_securite','a_ascenseur','a_monte_charge','accessibilite_pmr','normes_erp',
                'charges_incluses'
            ]:
                if champ_bool in doc and doc[champ_bool] is not None:
                    if isinstance(doc[champ_bool], str):
                        doc[champ_bool] = doc[champ_bool].lower() == 'true'
                    elif isinstance(doc[champ_bool], (int, float)):
                        doc[champ_bool] = bool(doc[champ_bool])
            
            for champ_int in ['nombre_sdb', 'nombre_vitrines', 'parking_nombre']:
                if champ_int in doc and doc[champ_int] is not None:
                    try:
                        doc[champ_int] = int(doc[champ_int]) if doc[champ_int] != 0 else None
                    except:
                        pass
            
            documents.append(doc)
        except Exception as e:
            erreurs.append((i, str(e)))
    
    if erreurs:
        print(f"⚠️ {len(erreurs)} locaux ont eu des erreurs lors de la préparation")
        for err in erreurs[:5]:
            print(f"   • Local {err[0]}: {err[1]}")
    
    print(f"✅ {len(documents)} locaux prêts à être insérés")
    
    # 5. VIDER LA COLLECTION
    print(f"\n🗑️ Nettoyage de la collection {NOM_COLLECTION}...")
    try:
        res_del = collection.delete_many({})
        print(f"✅ {res_del.deleted_count} anciens documents supprimés")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    # 6. INDEX
    print("\n🔧 Création des index...")
    try:
        collection.create_index("id"); print("✅ Index: id")
        collection.create_index("type_local"); print("✅ Index: type_local")
        collection.create_index("ville"); print("✅ Index: ville")
        collection.create_index("quartier"); print("✅ Index: quartier")
        collection.create_index("loyer"); print("✅ Index: loyer")
        collection.create_index("surface"); print("✅ Index: surface")
        collection.create_index("a_terrasse"); print("✅ Index: a_terrasse")
        collection.create_index("a_parking"); print("✅ Index: a_parking")
        collection.create_index("a_climatisation"); print("✅ Index: a_climatisation")
        collection.create_index("activites_possibles"); print("✅ Index: activites_possibles")
        
        if 'localisation' in locaux[0] and 'coordinates' in locaux[0].get('localisation', {}):
            collection.create_index([("localisation.coordinates", "2dsphere")])
            print("✅ Index géospatial créé")
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 7. INSERTION
    print(f"\n💾 Insertion de {len(documents)} locaux dans {NOM_COLLECTION}...")
    try:
        debut = time.time()
        resultat = collection.insert_many(documents, ordered=False)
        duree = time.time() - debut
        print(f"\n✅ {len(resultat.inserted_ids)} locaux insérés en {duree:.1f} secondes")
    except Exception as e:
        print(f"\n⚠️ Erreur insertion massive: {e}")
        print("🔄 Tentative par lots...")
        total_insere = 0
        taille_lot = 50
        for i in range(0, len(documents), taille_lot):
            lot = documents[i:i+taille_lot]
            try:
                r = collection.insert_many(lot, ordered=False)
                total_insere += len(r.inserted_ids)
                print(f"   ✅ Lot {i//taille_lot + 1}: {len(r.inserted_ids)} insérés")
            except:
                for doc in lot:
                    try:
                        collection.insert_one(doc)
                        total_insere += 1
                    except:
                        pass
        print(f"\n✅ Total inséré: {total_insere}/{len(documents)}")
    
    # 8. Vérification
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre de documents dans {NOM_COLLECTION}: {nombre_final}")
    print("\n✨ Vérifie sur MongoDB Atlas:")
    print("   Collections → EstateMind → Mubaweb.location.LocauxCommerciaux")
    
    client.close()
    print("\n🔒 Connexion fermée")

if __name__ == "__main__":
    inserer_location_locaux_commerciaux()