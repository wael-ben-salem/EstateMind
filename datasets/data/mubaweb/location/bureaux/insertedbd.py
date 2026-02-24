"""
SCRIPT D'INSERTION DES DONNÉES LOCATION BUREAUX DANS MONGODB ATLAS
Base de données: mubaweb
Collection: location_bureaux
Fichier: location_bureaux_clean.json (1180 locations de bureaux)
"""

import json
from pymongo import MongoClient
from datetime import datetime
import os
import time

def inserer_location_bureaux():
    print("="*70)
    print("🚀 INSERTION DES DONNÉES LOCATION BUREAUX DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: mubaweb")
    print("📁 Collection: location_bureaux")
    print("📊 Fichier: location_bureaux_clean.json (1180 locations de bureaux)")
    print("="*70)
    
    # === CONFIGURATION ===
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"              
    NOM_COLLECTION = "Mubaweb.location.Bureaux" 
    NOM_FICHIER = "location_bureaux_clean.json"
    
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
                    print(f"      • {region}: {stats_region.get('annonces_scrapees', 0)} bureaux")
            
            # Afficher les statistiques d'extraction
            if 'statistiques_extraction' in metadata:
                stats_extract = metadata['statistiques_extraction']
                print(f"\n   📊 Statistiques d'extraction:")
                print(f"      • Loyers extraits: {stats_extract.get('loyers_extraits', 0)}")
                print(f"      • Parkings détectés: {stats_extract.get('parkings_detectes', 0)}")
                print(f"      • Salles réunion détectées: {stats_extract.get('salles_reunion_detectees', 0)}")
                print(f"      • Kitchenettes détectées: {stats_extract.get('kitchenettes_detectees', 0)}")
                print(f"      • Fibres détectées: {stats_extract.get('fibres_detectees', 0)}")
                print(f"      • Nombres bureaux extraits: {stats_extract.get('nombres_bureaux_extraits', 0)}")
        
        # Extraire la liste des bureaux
        if isinstance(donnees, dict) and 'listings' in donnees:
            bureaux = donnees['listings']
        elif isinstance(donnees, list):
            bureaux = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_bureaux = len(bureaux)
        print(f"\n✅ {nombre_bureaux} locations de bureaux trouvées dans le fichier")
        
        # Vérification du nombre attendu
        if nombre_bureaux == 1180:
            print("✅ Nombre de bureaux conforme aux métadonnées (1180)")
        else:
            print(f"⚠️ Attention: {nombre_bureaux} trouvés, mais les métadonnées indiquent 1180")
        
        # Afficher les attributs disponibles
        if nombre_bureaux > 0:
            print("\n📋 Attributs spécifiques aux locations de bureaux:")
            attributs_specifiques = ['type_bureau', 'loyer', 'loyer_text', 'loyer_m2', 
                                    'nombre_bureaux', 'nombre_salles_reunion', 'est_open_space',
                                    'a_accueil', 'a_salle_reunion', 'a_kitchenette', 'a_fibre',
                                    'a_parking', 'a_stockage', 'charges_incluses', 'montant_charges']
            for attr in attributs_specifiques:
                if attr in bureaux[0]:
                    print(f"   • {attr}")
            
            # Afficher un exemple de bureau
            print("\n🔍 Exemple de bureau à louer (premier du fichier):")
            exemple = bureaux[0]
            champs_importants = ['id', 'titre', 'type_bureau', 'ville', 'quartier', 'surface', 
                                'loyer_text', 'nombre_bureaux', 'nombre_salles_reunion', 
                                'est_open_space', 'a_parking', 'a_fibre', 'a_kitchenette']
            for champ in champs_importants:
                if champ in exemple and exemple[champ] is not None:
                    valeur = exemple[champ]
                    if isinstance(valeur, bool):
                        valeur = "Oui" if valeur else "Non"
                    elif isinstance(valeur, float) and champ == 'surface':
                        valeur = f"{valeur} m²"
                    print(f"   • {champ}: {valeur}")
            
            # Afficher les équipements
            if 'equipements' in exemple and exemple['equipements']:
                print(f"   • équipements: {', '.join(exemple['equipements'][:5])}...")
            
    except Exception as e:
        print(f"❌ Erreur de lecture: {e}")
        return
    
    # 3. Connexion à MongoDB Atlas
    print(f"\n🔌 Connexion à MongoDB Atlas...")
    try:
        client = MongoClient(CHAINE_CONNEXION)
        # Vérifier la connexion
        client.admin.command('ping')
        print("✅ Connexion réussie!")
        
        # Sélectionner la base "mubaweb" et la collection "location_bureaux"
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
    
    for i, bureau in enumerate(bureaux):
        try:
            # Créer une copie pour ne pas modifier l'original
            doc = bureau.copy()
            
            # Ajouter des métadonnées MongoDB
            doc['_date_insertion'] = datetime.now()
            doc['_type_collection'] = 'location_bureaux'
            
            # S'assurer que l'ID est présent
            if 'id' not in doc:
                doc['id'] = str(i + 1)
            
            # Convertir les types si nécessaire
            if 'surface' in doc and doc['surface'] is not None:
                try:
                    doc['surface'] = float(doc['surface'])
                except:
                    pass
            
            if 'loyer' in doc and doc['loyer'] is not None:
                try:
                    doc['loyer'] = float(doc['loyer'])
                except:
                    pass
            
            if 'loyer_m2' in doc and doc['loyer_m2'] is not None:
                try:
                    doc['loyer_m2'] = float(doc['loyer_m2'])
                except:
                    pass
            
            if 'montant_charges' in doc and doc['montant_charges'] is not None:
                try:
                    doc['montant_charges'] = float(doc['montant_charges'])
                except:
                    pass
            
            # Convertir les booléens
            for champ_bool in ['est_open_space', 'est_immeuble_entier', 'a_accueil', 'a_salle_reunion',
                              'a_kitchenette', 'a_sanitaires', 'sanitaires_separes', 'a_parking',
                              'a_stockage', 'a_fibre', 'a_climatisation', 'a_chauffage',
                              'a_securite', 'a_ascenseur', 'ascenseur_panoramique', 'a_terrasse',
                              'acces_independant', 'a_moquette', 'charges_incluses']:
                if champ_bool in doc and doc[champ_bool] is not None:
                    if isinstance(doc[champ_bool], str):
                        doc[champ_bool] = doc[champ_bool].lower() == 'true'
                    elif isinstance(doc[champ_bool], (int, float)):
                        doc[champ_bool] = bool(doc[champ_bool])
            
            # Convertir les entiers
            for champ_int in ['nombre_pieces', 'nombre_bureaux', 'nombre_sdb', 'etage', 
                            'nombre_ascenseurs', 'parking_nombre', 'nombre_salles_reunion',
                            'nombre_sanitaires', 'nombre_etages_immeuble']:
                if champ_int in doc and doc[champ_int] is not None:
                    try:
                        doc[champ_int] = int(doc[champ_int]) if doc[champ_int] != 0 else None
                    except:
                        pass
            
            # Traiter les listes
            for champ in ['equipements', 'amenities_bureaux', 'proximites']:
                if champ in doc and isinstance(doc[champ], list):
                    # Garder comme liste
                    pass
            
            documents.append(doc)
            
        except Exception as e:
            erreurs.append((i, str(e)))
    
    if erreurs:
        print(f"⚠️ {len(erreurs)} bureaux ont eu des erreurs lors de la préparation")
        for err in erreurs[:5]:
            print(f"   • Bureau {err[0]}: {err[1]}")
    
    print(f"✅ {len(documents)} locations de bureaux prêtes à être insérées sur {nombre_bureaux}")
    
    # 5. VIDER LA COLLECTION (pour éviter les doublons)
    print(f"\n🗑️ Nettoyage de la collection {NOM_COLLECTION}...")
    try:
        resultat_suppression = collection.delete_many({})
        print(f"✅ {resultat_suppression.deleted_count} anciens documents supprimés")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    # 6. CRÉER DES INDEX POUR OPTIMISER LES RECHERCHES
    print("\n🔧 Création des index...")
    try:
        # Index sur l'ID
        collection.create_index("id", unique=False)
        print("✅ Index créé sur le champ 'id'")
        
        # Index sur le type de bureau
        collection.create_index("type_bureau")
        print("✅ Index créé sur le champ 'type_bureau'")
        
        # Index sur la ville
        collection.create_index("ville")
        print("✅ Index créé sur le champ 'ville'")
        
        # Index sur le quartier
        collection.create_index("quartier")
        print("✅ Index créé sur le champ 'quartier'")
        
        # Index sur le loyer
        collection.create_index("loyer")
        print("✅ Index créé sur le champ 'loyer'")
        
        # Index sur la surface
        collection.create_index("surface")
        print("✅ Index créé sur le champ 'surface'")
        
        # Index sur le nombre de bureaux
        collection.create_index("nombre_bureaux")
        print("✅ Index créé sur le champ 'nombre_bureaux'")
        
        # Index sur les caractéristiques importantes
        collection.create_index("est_open_space")
        print("✅ Index créé sur le champ 'est_open_space'")
        
        collection.create_index("a_salle_reunion")
        print("✅ Index créé sur le champ 'a_salle_reunion'")
        
        collection.create_index("a_kitchenette")
        print("✅ Index créé sur le champ 'a_kitchenette'")
        
        collection.create_index("a_parking")
        print("✅ Index créé sur le champ 'a_parking'")
        
        collection.create_index("a_fibre")
        print("✅ Index créé sur le champ 'a_fibre'")
        
        collection.create_index("a_climatisation")
        print("✅ Index créé sur le champ 'a_climatisation'")
        
        collection.create_index("a_ascenseur")
        print("✅ Index créé sur le champ 'a_ascenseur'")
        
        # Index géospatial
        if 'localisation' in bureaux[0] and 'coordinates' in bureaux[0].get('localisation', {}):
            collection.create_index([("localisation.coordinates", "2dsphere")])
            print("✅ Index géospatial créé")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 7. INSÉRER TOUS LES DOCUMENTS (1180 bureaux)
    print(f"\n💾 Insertion de {len(documents)} locations de bureaux dans location_bureaux...")
    print("   Insertion par lots de 100 documents pour optimiser les performances...")
    
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
                print(f"   ✅ Lot {i//taille_lot + 1}: {len(resultat_lot.inserted_ids)} bureaux insérés ({pourcentage:.1f}%)")
            except Exception as e_lot:
                print(f"   ⚠️ Lot {i//taille_lot + 1}: Erreur - insertion individuelle...")
                for doc in lot:
                    try:
                        collection.insert_one(doc)
                        total_insere += 1
                    except Exception as e_doc:
                        print(f"      ✗ Bureau {doc.get('id', 'inconnu')} non inséré: {str(e_doc)[:50]}")
        
        duree = time.time() - debut
        print(f"\n✅ Total inséré: {total_insere}/{len(documents)} bureaux en {duree:.1f} secondes")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion: {e}")
    
    # 8. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre de bureaux dans location_bureaux: {nombre_final}")
    
    if nombre_final == len(documents):
        print("✅ SUCCÈS TOTAL: Tous les bureaux à louer sont présents!")
    elif nombre_final > 0:
        pourcentage = (nombre_final / len(documents)) * 100
        print(f"⚠️ Partiel: {nombre_final}/{len(documents)} bureaux présents ({pourcentage:.1f}%)")
    else:
        print("❌ Aucun bureau n'a été inséré")
    
    # 9. Afficher un échantillon des données insérées
    if nombre_final > 0:
        print("\n🔍 Échantillon des bureaux à louer insérés:")
        bureaux_exemples = collection.find().limit(3)
        for i, bureau in enumerate(bureaux_exemples, 1):
            print(f"\n   🏢 Bureau {i}:")
            print(f"      • ID: {bureau.get('id', 'N/A')}")
            print(f"      • Type: {bureau.get('type_bureau', 'N/A')}")
            print(f"      • Titre: {bureau.get('titre', 'N/A')[:60]}...")
            print(f"      • Ville: {bureau.get('ville', 'N/A')}")
            print(f"      • Quartier: {bureau.get('quartier', 'N/A')}")
            print(f"      • Surface: {bureau.get('surface', 'N/A')} m²")
            print(f"      • Loyer: {bureau.get('loyer_text', 'N/A')}")
            print(f"      • Open space: {'Oui' if bureau.get('est_open_space') else 'Non'}")
            print(f"      • Nombre de bureaux: {bureau.get('nombre_bureaux', 'N/A')}")
            print(f"      • Salle réunion: {'Oui' if bureau.get('a_salle_reunion') else 'Non'}")
            print(f"      • Kitchenette: {'Oui' if bureau.get('a_kitchenette') else 'Non'}")
            print(f"      • Fibre: {'Oui' if bureau.get('a_fibre') else 'Non'}")
            print(f"      • Parking: {'Oui' if bureau.get('a_parking') else 'Non'}")
            print(f"      • Climatisation: {'Oui' if bureau.get('a_climatisation') else 'Non'}")
    
    # 10. Statistiques détaillées
    print("\n" + "="*70)
    print("📊 STATISTIQUES DES LOCATIONS DE BUREAUX")
    print("="*70)
    
    try:
        # 1. Répartition par type de bureau
        print("\n🏷️ Par type de bureau:")
        types = collection.aggregate([
            {"$group": {"_id": "$type_bureau", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for t in types:
            if t['_id']:
                print(f"   • {t['_id']}: {t['count']} bureaux")
        
        # 2. Répartition par ville
        print("\n📍 Par ville:")
        villes = collection.aggregate([
            {"$group": {"_id": "$ville", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for v in villes:
            if v['_id']:
                print(f"   • {v['_id']}: {v['count']} bureaux")
        
        # 3. Statistiques des caractéristiques
        print("\n✨ Caractéristiques:")
        
        # Open space
        open_space = collection.aggregate([
            {"$match": {"est_open_space": True}},
            {"$count": "total"}
        ])
        for o in open_space:
            print(f"   • Open space: {o['total']} bureaux ({o['total']/nombre_final*100:.1f}%)")
        
        # Salle réunion
        salle_reunion = collection.aggregate([
            {"$match": {"a_salle_reunion": True}},
            {"$count": "total"}
        ])
        for s in salle_reunion:
            print(f"   • Avec salle de réunion: {s['total']} bureaux ({s['total']/nombre_final*100:.1f}%)")
        
        # Kitchenette
        kitchenette = collection.aggregate([
            {"$match": {"a_kitchenette": True}},
            {"$count": "total"}
        ])
        for k in kitchenette:
            print(f"   • Avec kitchenette: {k['total']} bureaux ({k['total']/nombre_final*100:.1f}%)")
        
        # Parking
        parking = collection.aggregate([
            {"$match": {"a_parking": True}},
            {"$count": "total"}
        ])
        for p in parking:
            print(f"   • Avec parking: {p['total']} bureaux ({p['total']/nombre_final*100:.1f}%)")
        
        # Fibre
        fibre = collection.aggregate([
            {"$match": {"a_fibre": True}},
            {"$count": "total"}
        ])
        for f in fibre:
            print(f"   • Avec fibre optique: {f['total']} bureaux ({f['total']/nombre_final*100:.1f}%)")
        
        # Climatisation
        climatisation = collection.aggregate([
            {"$match": {"a_climatisation": True}},
            {"$count": "total"}
        ])
        for c in climatisation:
            print(f"   • Avec climatisation: {c['total']} bureaux ({c['total']/nombre_final*100:.1f}%)")
        
        # Accueil
        accueil = collection.aggregate([
            {"$match": {"a_accueil": True}},
            {"$count": "total"}
        ])
        for a in accueil:
            print(f"   • Avec espace accueil: {a['total']} bureaux ({a['total']/nombre_final*100:.1f}%)")
        
        # 4. Statistiques de surface
        stats_surface = collection.aggregate([
            {"$match": {"surface": {"$exists": True, "$ne": None, "$ne": 0}}},
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
        
        # 5. Statistiques de loyer
        stats_loyer = collection.aggregate([
            {"$match": {"loyer": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$loyer"},
                "max": {"$max": "$loyer"},
                "moyen": {"$avg": "$loyer"},
                "total": {"$sum": 1}
            }}
        ])
        for s in stats_loyer:
            print(f"\n💰 Loyers:")
            print(f"   • Min: {s['min']:,.0f} TND")
            print(f"   • Max: {s['max']:,.0f} TND")
            print(f"   • Moyen: {s['moyen']:,.0f} TND")
            print(f"   • Bureaux avec loyer affiché: {s['total']}")
        
        # 6. Répartition par nombre de bureaux
        print("\n📊 Par nombre de bureaux:")
        nb_bureaux = collection.aggregate([
            {"$match": {"nombre_bureaux": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {"_id": "$nombre_bureaux", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
            {"$limit": 10}
        ])
        for n in nb_bureaux:
            if n['_id']:
                print(f"   • {n['_id']} bureau(x): {n['count']} locaux")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du calcul des statistiques: {e}")
    
    # 11. Récapitulatif de toutes les collections
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF BASE DE DONNÉES mubaweb")
    print("="*70)
    
    try:
        collections_info = {}
        for nom_collection in db.list_collection_names():
            count = db[nom_collection].count_documents({})
            collections_info[nom_collection] = count
        
        # Afficher dans un ordre spécifique
        collections_ordre = ['vente_appartements', 'vente_villas', 'vente_terrains', 
                           'vente_maisons', 'vente_locaux_commerciaux', 
                           'location_appartements', 'location_bureaux', 
                           'location_locaux_commerciaux', 'locationNeuf', 
                           'locations_vacances']
        
        for nom in collections_ordre:
            if nom in collections_info:
                print(f"📍 Collection '{nom}': {collections_info[nom]} documents")
        
        # Afficher les autres collections
        for nom, count in collections_info.items():
            if nom not in collections_ordre:
                print(f"📍 Collection '{nom}': {count} documents")
        
        total_documents = sum(collections_info.values())
        print(f"\n📌 TOTAL GÉNÉRAL: {total_documents} documents dans la base mubaweb")
        
        # Vérification spéciale pour location_bureaux
        if 'location_bureaux' in collections_info:
            if collections_info['location_bureaux'] == 1180:
                print("✅ Les 1180 locations de bureaux ont bien été insérées!")
            else:
                print(f"⚠️ Attention: {collections_info['location_bureaux']}/1180 bureaux insérés")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du récapitulatif: {e}")
    
    # Fermer la connexion
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ Vous pouvez maintenant vérifier vos locations de bureaux sur MongoDB Atlas:")
    print("   https://cloud.mongodb.com/ → Collections → EstateMind → Mubaweb.location.Bureaux")

if __name__ == "__main__":
    inserer_location_bureaux()