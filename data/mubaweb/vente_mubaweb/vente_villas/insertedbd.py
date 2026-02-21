"""
SCRIPT D'INSERTION DES DONNÉES VILLAS DANS MONGODB ATLAS
Base de données: EstateMind
Collection: Mubaweb.vente.Villas
Fichier: villas_clean.json (1367 villas de luxe)
"""

import json
from pymongo import MongoClient
from datetime import datetime
import os
import time

def inserer_vente_villas():
    print("="*70)
    print("🚀 INSERTION DES DONNÉES VILLAS DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: EstateMind")
    print("📁 Collection: Mubaweb.vente.Villas")
    print("📊 Fichier: villas_clean.json (1367 villas de luxe)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"            # ✅ CHANGÉ
    NOM_COLLECTION  = "Mubaweb.vente.Villas"   # ✅ CHANGÉ
    NOM_FICHIER     = "villas_clean.json"
    
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
                    print(f"      • {region}: {stats_region.get('annonces_scrapees', 0)} villas")
            
            if 'statistiques_extraction' in metadata:
                stats_extract = metadata['statistiques_extraction']
                print(f"\n   📊 Statistiques d'extraction:")
                print(f"      • Piscines détectées: {stats_extract.get('piscines_detectees', 0)}")
                print(f"      • Spas détectés: {stats_extract.get('spas_detectes', 0)}")
                print(f"      • Hammams détectés: {stats_extract.get('hammams_detectes', 0)}")
                print(f"      • Jardins détectés: {stats_extract.get('jardins_detectes', 0)}")
                print(f"      • Terrasses détectées: {stats_extract.get('terrasses_detectees', 0)}")
                print(f"      • Surfaces terrain extraites: {stats_extract.get('surfaces_terrain_extraites', 0)}")
        
        # Extraire la liste des villas
        if isinstance(donnees, dict) and 'listings' in donnees:
            villas = donnees['listings']
        elif isinstance(donnees, list):
            villas = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_villas = len(villas)
        print(f"\n✅ {nombre_villas} villas trouvées dans le fichier")
        
        # Vérification du nombre attendu
        if nombre_villas == 1367:
            print("✅ Nombre de villas conforme aux métadonnées (1367)")
        else:
            print(f"⚠️ Attention: {nombre_villas} trouvées, mais les métadonnées indiquent 1367")
        
        # Afficher les attributs disponibles
        if nombre_villas > 0:
            print("\n📋 Attributs spécifiques aux villas de luxe:")
            attributs_specifiques = ['type_villa', 'style_architectural', 'niveau_standing', 
                                    'surface_terrain', 'a_piscine', 'a_spa', 'a_hammam',
                                    'a_home_cinema', 'a_cave_vin', 'type_piscine', 'vue']
            for attr in attributs_specifiques:
                if attr in villas[0]:
                    print(f"   • {attr}")
            
            # Afficher un exemple de villa
            print("\n🔍 Exemple de villa (première du fichier):")
            exemple = villas[0]
            champs_importants = ['id', 'titre', 'type_villa', 'ville', 'quartier', 'surface', 
                                'surface_terrain', 'prix_text', 'a_piscine', 'a_spa', 'a_hammam',
                                'nombre_chambres', 'nombre_sdb', 'niveau_standing']
            for champ in champs_importants:
                if champ in exemple and exemple[champ] is not None:
                    valeur = exemple[champ]
                    if isinstance(valeur, bool):
                        valeur = "Oui" if valeur else "Non"
                    elif isinstance(valeur, float) and champ in ['surface', 'surface_terrain']:
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
        
        # ✅ Base: EstateMind | Collection: Mubaweb.vente.Villas
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
    
    for i, villa in enumerate(villas):
        try:
            doc = villa.copy()
            doc['_date_insertion'] = datetime.now()
            doc['_type_collection'] = 'vente_villas'
            
            if 'id' not in doc:
                doc['id'] = str(i + 1)
            
            if 'surface' in doc and doc['surface'] is not None:
                try: doc['surface'] = float(doc['surface'])
                except: pass
            
            if 'surface_terrain' in doc and doc['surface_terrain'] is not None:
                try: doc['surface_terrain'] = float(doc['surface_terrain'])
                except: pass
            
            if 'prix' in doc and doc['prix'] is not None:
                try: doc['prix'] = float(doc['prix'])
                except: pass
            
            if 'prix_m2' in doc and doc['prix_m2'] is not None:
                try: doc['prix_m2'] = float(doc['prix_m2'])
                except: pass
            
            for champ_bool in [
                'a_piscine', 'a_spa', 'a_hammam', 'a_jardin', 'a_terrasse',
                'a_garage', 'a_cheminee', 'a_home_cinema', 'a_cave_vin',
                'a_bureau', 'a_dressing', 'a_buanderie', 'a_cellier',
                'a_alarme', 'a_panneaux_solaires'
            ]:
                if champ_bool in doc and doc[champ_bool] is not None:
                    if isinstance(doc[champ_bool], str):
                        doc[champ_bool] = doc[champ_bool].lower() == 'true'
                    elif isinstance(doc[champ_bool], (int, float)):
                        doc[champ_bool] = bool(doc[champ_bool])
            
            for champ_int in [
                'nombre_pieces', 'nombre_chambres', 'nombre_sdb', 'nombre_etages',
                'nombre_suites', 'garage_nombre'
            ]:
                if champ_int in doc and doc[champ_int] is not None:
                    try:
                        doc[champ_int] = int(doc[champ_int]) if doc[champ_int] != 0 else None
                    except:
                        pass
            
            documents.append(doc)
            
        except Exception as e:
            erreurs.append((i, str(e)))
    
    if erreurs:
        print(f"⚠️ {len(erreurs)} villas ont eu des erreurs lors de la préparation")
        for err in erreurs[:5]:
            print(f"   • Villa {err[0]}: {err[1]}")
    
    print(f"✅ {len(documents)} villas prêtes à être insérées sur {nombre_villas}")
    
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
        collection.create_index("type_villa"); print("✅ Index: type_villa")
        collection.create_index("niveau_standing"); print("✅ Index: niveau_standing")
        collection.create_index("ville"); print("✅ Index: ville")
        collection.create_index("quartier"); print("✅ Index: quartier")
        collection.create_index("prix"); print("✅ Index: prix")
        collection.create_index("surface"); print("✅ Index: surface")
        collection.create_index("surface_terrain"); print("✅ Index: surface_terrain")
        collection.create_index("a_piscine"); print("✅ Index: a_piscine")
        collection.create_index("a_spa"); print("✅ Index: a_spa")
        collection.create_index("a_hammam"); print("✅ Index: a_hammam")
        collection.create_index("a_jardin"); print("✅ Index: a_jardin")
        collection.create_index("a_home_cinema"); print("✅ Index: a_home_cinema")
        collection.create_index("nombre_chambres"); print("✅ Index: nombre_chambres")
        
        if 'localisation' in villas[0] and 'coordinates' in villas[0].get('localisation', {}):
            collection.create_index([("localisation.coordinates", "2dsphere")])
            print("✅ Index géospatial créé")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 7. INSÉRER (1367 villas) - lots de 100
    print(f"\n💾 Insertion de {len(documents)} villas dans {NOM_COLLECTION}...")
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
                print(f"   ✅ Lot {i//taille_lot + 1}: {len(resultat_lot.inserted_ids)} villas ({pourcentage:.1f}%)")
            except Exception as e_lot:
                print(f"   ⚠️ Lot {i//taille_lot + 1}: insertion individuelle...")
                for doc in lot:
                    try:
                        collection.insert_one(doc)
                        total_insere += 1
                    except Exception as e_doc:
                        print(f"      ✗ Villa {doc.get('id', 'inconnu')} non insérée: {str(e_doc)[:50]}")
        
        duree = time.time() - debut
        print(f"\n✅ Total inséré: {total_insere}/{len(documents)} villas en {duree:.1f} secondes")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion: {e}")
    
    # 8. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre de villas dans {NOM_COLLECTION}: {nombre_final}")
    
    if nombre_final == len(documents):
        print("✅ SUCCÈS TOTAL: Toutes les villas sont présentes!")
    elif nombre_final > 0:
        pourcentage = (nombre_final / len(documents)) * 100
        print(f"⚠️ Partiel: {nombre_final}/{len(documents)} villas présentes ({pourcentage:.1f}%)")
    else:
        print("❌ Aucune villa n'a été insérée")
    
    # 9. Échantillon
    if nombre_final > 0:
        print("\n🔍 Échantillon des villas insérées:")
        villas_exemples = collection.find().limit(3)
        for i, v in enumerate(villas_exemples, 1):
            print(f"\n   🏰 Villa {i}:")
            print(f"      • ID: {v.get('id', 'N/A')}")
            print(f"      • Type: {v.get('type_villa', 'N/A')}")
            print(f"      • Standing: {v.get('niveau_standing', 'N/A')}")
            print(f"      • Ville: {v.get('ville', 'N/A')}")
            print(f"      • Surface: {v.get('surface', 'N/A')} m²")
            if v.get('surface_terrain'):
                print(f"      • Terrain: {v.get('surface_terrain')} m²")
            print(f"      • Prix: {v.get('prix_text', 'N/A')}")
    
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
            "Mubaweb.vente.Maisons",
            "Mubaweb.vente.Villas",
            "Mubaweb.locationNeuf",
            "Mubaweb.locations_vacances",
        ]
        for nom in ordre:
            if nom in collections_info:
                print(f"📍 Collection '{nom}': {collections_info[nom]} documents")
        for nom, count in collections_info.items():
            if nom not in ordre:
                print(f"📍 Collection '{nom}': {count} documents")
        
        print(f"\n📌 TOTAL GÉNÉRAL: {sum(collections_info.values())} documents dans EstateMind")
        if NOM_COLLECTION in collections_info:
            if collections_info[NOM_COLLECTION] == 1367:
                print("✅ Les 1367 villas ont bien été insérées!")
            else:
                print(f"⚠️ Attention: {collections_info[NOM_COLLECTION]}/1367 villas insérées")
    except Exception as e:
        print(f"⚠️ Erreur lors du récapitulatif: {e}")
    
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ Vérifie sur MongoDB Atlas:")
    print("   Collections → EstateMind → Mubaweb.vente.Villas")

if __name__ == "__main__":
    inserer_vente_villas()
