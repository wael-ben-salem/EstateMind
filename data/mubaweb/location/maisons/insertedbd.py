"""
SCRIPT D'INSERTION DES DONNÉES LOCATION MAISONS DANS MONGODB ATLAS
Base de données: mubaweb
Collection: location_maisons
Fichier: location_maisons_clean.json (322 locations de maisons)
"""

import json
from pymongo import MongoClient
from datetime import datetime
import os
import time

def inserer_location_maisons():
    print("="*70)
    print("🚀 INSERTION DES DONNÉES LOCATION MAISONS DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: mubaweb")
    print("📁 Collection: location_maisons")
    print("📊 Fichier: location_maisons_clean.json (322 locations de maisons)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"                
    NOM_COLLECTION = "Mubaweb.location.Maisons" 
    NOM_FICHIER = "location_maisons_clean.json"
    
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
                    print(f"      • {region}: {stats_region.get('annonces_scrapees', 0)} maisons")
            
            # Afficher les statistiques d'extraction
            if 'statistiques_extraction' in metadata:
                stats_extract = metadata['statistiques_extraction']
                print(f"\n   📊 Statistiques d'extraction:")
                print(f"      • Loyers extraits: {stats_extract.get('loyers_extraits', 0)}")
                print(f"      • Jardins détectés: {stats_extract.get('jardins_detectes', 0)}")
                print(f"      • Piscines détectées: {stats_extract.get('piscines_detectees', 0)}")
                print(f"      • Terrasses détectées: {stats_extract.get('terrasses_detectees', 0)}")
                print(f"      • Garages détectés: {stats_extract.get('garages_detectes', 0)}")
                print(f"      • Vues mer détectées: {stats_extract.get('vues_mer_detectees', 0)}")
                print(f"      • Quartiers sécurisés: {stats_extract.get('quartiers_securises', 0)}")
        
        # Extraire la liste des maisons
        if isinstance(donnees, dict) and 'listings' in donnees:
            maisons = donnees['listings']
        elif isinstance(donnees, list):
            maisons = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_maisons = len(maisons)
        print(f"\n✅ {nombre_maisons} locations de maisons trouvées dans le fichier")
        
        # Vérification du nombre attendu
        if nombre_maisons == 322:
            print("✅ Nombre de maisons conforme aux métadonnées (322)")
        else:
            print(f"⚠️ Attention: {nombre_maisons} trouvées, mais les métadonnées indiquent 322")
        
        # Afficher les attributs disponibles
        if nombre_maisons > 0:
            print("\n📋 Attributs spécifiques aux locations de maisons:")
            attributs_specifiques = ['type_maison', 'loyer', 'loyer_text', 'loyer_m2', 
                                    'surface_jardin', 'surface_terrasse', 'est_partagee',
                                    'a_jardin', 'a_piscine', 'a_terrasse', 'a_garage',
                                    'quartier_securise', 'animaux_acceptes', 'profil_locataire',
                                    'surface_terrain', 'nombre_niveaux']
            for attr in attributs_specifiques:
                if attr in maisons[0]:
                    print(f"   • {attr}")
            
            # Afficher un exemple de maison
            print("\n🔍 Exemple de maison à louer (première du fichier):")
            exemple = maisons[0]
            champs_importants = ['id', 'titre', 'type_maison', 'ville', 'quartier', 'surface', 
                                'surface_jardin', 'surface_terrasse', 'loyer_text', 'nombre_pieces',
                                'nombre_chambres', 'a_jardin', 'a_piscine', 'a_terrasse', 'a_garage',
                                'quartier_securise', 'vue', 'profil_locataire']
            for champ in champs_importants:
                if champ in exemple and exemple[champ] is not None:
                    valeur = exemple[champ]
                    if isinstance(valeur, bool):
                        valeur = "Oui" if valeur else "Non"
                    elif isinstance(valeur, float) and champ in ['surface', 'surface_jardin', 'surface_terrasse']:
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
        
        # Sélectionner la base "mubaweb" et la collection "location_maisons"
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
    
    for i, maison in enumerate(maisons):
        try:
            # Créer une copie pour ne pas modifier l'original
            doc = maison.copy()
            
            # Ajouter des métadonnées MongoDB
            doc['_date_insertion'] = datetime.now()
            doc['_type_collection'] = 'location_maisons'
            
            # S'assurer que l'ID est présent
            if 'id' not in doc:
                doc['id'] = str(i + 1)
            
            # Convertir les types si nécessaire
            if 'surface' in doc and doc['surface'] is not None:
                try:
                    doc['surface'] = float(doc['surface'])
                except:
                    pass
            
            if 'surface_jardin' in doc and doc['surface_jardin'] is not None:
                try:
                    doc['surface_jardin'] = float(doc['surface_jardin'])
                except:
                    pass
            
            if 'surface_terrasse' in doc and doc['surface_terrasse'] is not None:
                try:
                    doc['surface_terrasse'] = float(doc['surface_terrasse'])
                except:
                    pass
            
            if 'surface_terrain' in doc and doc['surface_terrain'] is not None:
                try:
                    doc['surface_terrain'] = float(doc['surface_terrain'])
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
            
            # Convertir les booléens
            for champ_bool in ['est_partagee', 'a_jardin', 'a_piscine', 'a_terrasse', 'a_balcon',
                              'a_garage', 'a_cave', 'a_buanderie', 'a_chambre_service', 'a_dressing',
                              'a_cheminee', 'a_climatisation', 'a_chauffage', 'a_securite',
                              'quartier_calme', 'quartier_securise', 'animaux_acceptes', 'meuble',
                              'charges_incluses']:
                if champ_bool in doc and doc[champ_bool] is not None:
                    if isinstance(doc[champ_bool], str):
                        doc[champ_bool] = doc[champ_bool].lower() == 'true'
                    elif isinstance(doc[champ_bool], (int, float)):
                        doc[champ_bool] = bool(doc[champ_bool])
            
            # Convertir les entiers
            for champ_int in ['nombre_pieces', 'nombre_chambres', 'nombre_sdb', 'nombre_niveaux',
                            'garage_nombre', 'nombre_balcons']:
                if champ_int in doc and doc[champ_int] is not None:
                    try:
                        doc[champ_int] = int(doc[champ_int]) if doc[champ_int] != 0 else None
                    except:
                        pass
            
            # Traiter les listes
            for champ in ['equipements', 'amenities_maison', 'proximites', 'materiaux']:
                if champ in doc and isinstance(doc[champ], list):
                    # Garder comme liste
                    pass
            
            documents.append(doc)
            
        except Exception as e:
            erreurs.append((i, str(e)))
    
    if erreurs:
        print(f"⚠️ {len(erreurs)} maisons ont eu des erreurs lors de la préparation")
        for err in erreurs[:5]:
            print(f"   • Maison {err[0]}: {err[1]}")
    
    print(f"✅ {len(documents)} locations de maisons prêtes à être insérées sur {nombre_maisons}")
    
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
        
        # Index sur le type de maison
        collection.create_index("type_maison")
        print("✅ Index créé sur le champ 'type_maison'")
        
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
        
        # Index sur le nombre de pièces
        collection.create_index("nombre_pieces")
        print("✅ Index créé sur le champ 'nombre_pieces'")
        
        # Index sur le nombre de chambres
        collection.create_index("nombre_chambres")
        print("✅ Index créé sur le champ 'nombre_chambres'")
        
        # Index sur les caractéristiques importantes
        collection.create_index("a_jardin")
        print("✅ Index créé sur le champ 'a_jardin'")
        
        collection.create_index("a_piscine")
        print("✅ Index créé sur le champ 'a_piscine'")
        
        collection.create_index("a_terrasse")
        print("✅ Index créé sur le champ 'a_terrasse'")
        
        collection.create_index("a_garage")
        print("✅ Index créé sur le champ 'a_garage'")
        
        collection.create_index("quartier_securise")
        print("✅ Index créé sur le champ 'quartier_securise'")
        
        collection.create_index("animaux_acceptes")
        print("✅ Index créé sur le champ 'animaux_acceptes'")
        
        collection.create_index("vue")
        print("✅ Index créé sur le champ 'vue'")
        
        collection.create_index("profil_locataire")
        print("✅ Index créé sur le champ 'profil_locataire'")
        
        # Index géospatial
        if 'localisation' in maisons[0] and 'coordinates' in maisons[0].get('localisation', {}):
            collection.create_index([("localisation.coordinates", "2dsphere")])
            print("✅ Index géospatial créé")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 7. INSÉRER TOUS LES DOCUMENTS (322 maisons)
    print(f"\n💾 Insertion de {len(documents)} locations de maisons dans location_maisons...")
    
    try:
        # Insertion en une seule fois (322 documents)
        debut = time.time()
        resultat = collection.insert_many(documents, ordered=False)
        duree = time.time() - debut
        
        print(f"\n✅ {len(resultat.inserted_ids)} locations de maisons insérées en {duree:.1f} secondes")
        
    except Exception as e:
        print(f"\n⚠️ Erreur lors de l'insertion massive: {e}")
        print("\n🔄 Tentative d'insertion par lots...")
        
        try:
            total_insere = 0
            taille_lot = 50
            
            for i in range(0, len(documents), taille_lot):
                lot = documents[i:i+taille_lot]
                try:
                    resultat_lot = collection.insert_many(lot, ordered=False)
                    total_insere += len(resultat_lot.inserted_ids)
                    print(f"   ✅ Lot {i//taille_lot + 1}: {len(resultat_lot.inserted_ids)} maisons insérées")
                except Exception as e_lot:
                    print(f"   ⚠️ Lot {i//taille_lot + 1}: Insertion individuelle...")
                    for doc in lot:
                        try:
                            collection.insert_one(doc)
                            total_insere += 1
                        except Exception as e_doc:
                            print(f"      ✗ Maison {doc.get('id', 'inconnu')} non insérée: {str(e_doc)[:50]}")
            
            print(f"\n✅ Total inséré: {total_insere}/{len(documents)} maisons")
            
        except Exception as e2:
            print(f"❌ Échec de l'insertion: {e2}")
    
    # 8. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre de maisons dans location_maisons: {nombre_final}")
    
    if nombre_final == len(documents):
        print("✅ SUCCÈS TOTAL: Toutes les maisons à louer sont présentes!")
    elif nombre_final > 0:
        pourcentage = (nombre_final / len(documents)) * 100
        print(f"⚠️ Partiel: {nombre_final}/{len(documents)} maisons présentes ({pourcentage:.1f}%)")
    else:
        print("❌ Aucune maison n'a été insérée")
    
    # 9. Afficher un échantillon des données insérées
    if nombre_final > 0:
        print("\n🔍 Échantillon des maisons à louer insérées:")
        maisons_exemples = collection.find().limit(3)
        for i, maison in enumerate(maisons_exemples, 1):
            print(f"\n   🏠 Maison {i}:")
            print(f"      • ID: {maison.get('id', 'N/A')}")
            print(f"      • Type: {maison.get('type_maison', 'N/A')}")
            print(f"      • Titre: {maison.get('titre', 'N/A')[:60]}...")
            print(f"      • Ville: {maison.get('ville', 'N/A')}")
            print(f"      • Quartier: {maison.get('quartier', 'N/A')}")
            print(f"      • Surface: {maison.get('surface', 'N/A')} m²")
            if maison.get('surface_jardin'):
                print(f"      • Jardin: {maison.get('surface_jardin')} m²")
            if maison.get('surface_terrasse'):
                print(f"      • Terrasse: {maison.get('surface_terrasse')} m²")
            print(f"      • Loyer: {maison.get('loyer_text', 'N/A')}")
            print(f"      • Jardin: {'Oui' if maison.get('a_jardin') else 'Non'}")
            print(f"      • Piscine: {'Oui' if maison.get('a_piscine') else 'Non'}")
            print(f"      • Terrasse: {'Oui' if maison.get('a_terrasse') else 'Non'}")
            print(f"      • Garage: {'Oui' if maison.get('a_garage') else 'Non'}")
            print(f"      • Quartier sécurisé: {'Oui' if maison.get('quartier_securise') else 'Non'}")
            print(f"      • Animaux acceptés: {'Oui' if maison.get('animaux_acceptes') else 'Non'}")
            print(f"      • Pièces: {maison.get('nombre_pieces', 'N/A')}")
            print(f"      • Chambres: {maison.get('nombre_chambres', 'N/A')}")
            if maison.get('vue'):
                print(f"      • Vue: {maison.get('vue')}")
    
    # 10. Statistiques détaillées
    print("\n" + "="*70)
    print("📊 STATISTIQUES DES LOCATIONS DE MAISONS")
    print("="*70)
    
    try:
        # 1. Répartition par type de maison
        print("\n🏷️ Par type de maison:")
        types = collection.aggregate([
            {"$group": {"_id": "$type_maison", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for t in types:
            if t['_id']:
                print(f"   • {t['_id']}: {t['count']} maisons")
        
        # 2. Répartition par quartier
        print("\n📍 Par quartier:")
        quartiers = collection.aggregate([
            {"$group": {"_id": "$quartier", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ])
        for q in quartiers:
            if q['_id']:
                print(f"   • {q['_id']}: {q['count']} maisons")
        
        # 3. Statistiques des caractéristiques
        print("\n✨ Caractéristiques:")
        
        # Jardin
        jardin = collection.aggregate([
            {"$match": {"a_jardin": True}},
            {"$count": "total"}
        ])
        for j in jardin:
            print(f"   • Avec jardin: {j['total']} maisons ({j['total']/nombre_final*100:.1f}%)")
        
        # Piscine
        piscine = collection.aggregate([
            {"$match": {"a_piscine": True}},
            {"$count": "total"}
        ])
        for p in piscine:
            print(f"   • Avec piscine: {p['total']} maisons ({p['total']/nombre_final*100:.1f}%)")
        
        # Terrasse
        terrasse = collection.aggregate([
            {"$match": {"a_terrasse": True}},
            {"$count": "total"}
        ])
        for t in terrasse:
            print(f"   • Avec terrasse: {t['total']} maisons ({t['total']/nombre_final*100:.1f}%)")
        
        # Garage
        garage = collection.aggregate([
            {"$match": {"a_garage": True}},
            {"$count": "total"}
        ])
        for g in garage:
            print(f"   • Avec garage: {g['total']} maisons ({g['total']/nombre_final*100:.1f}%)")
        
        # Quartier sécurisé
        securise = collection.aggregate([
            {"$match": {"quartier_securise": True}},
            {"$count": "total"}
        ])
        for s in securise:
            print(f"   • Quartier sécurisé: {s['total']} maisons ({s['total']/nombre_final*100:.1f}%)")
        
        # Animaux acceptés
        animaux = collection.aggregate([
            {"$match": {"animaux_acceptes": True}},
            {"$count": "total"}
        ])
        for a in animaux:
            print(f"   • Animaux acceptés: {a['total']} maisons")
        
        # Vue mer
        vue_mer = collection.aggregate([
            {"$match": {"vue": "Mer"}},
            {"$count": "total"}
        ])
        for v in vue_mer:
            print(f"   • Vue sur mer: {v['total']} maisons")
        
        # 4. Statistiques de surface habitable
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
            print(f"\n📐 Surfaces habitables:")
            print(f"   • Min: {s['min']:,.0f} m²")
            print(f"   • Max: {s['max']:,.0f} m²")
            print(f"   • Moyenne: {s['moyen']:,.0f} m²")
        
        # 5. Statistiques de jardin (pour celles qui ont un jardin)
        stats_jardin = collection.aggregate([
            {"$match": {"surface_jardin": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$surface_jardin"},
                "max": {"$max": "$surface_jardin"},
                "moyen": {"$avg": "$surface_jardin"},
                "total": {"$sum": 1}
            }}
        ])
        for s in stats_jardin:
            if s['total'] > 0:
                print(f"\n🌳 Surfaces jardin:")
                print(f"   • Min: {s['min']:,.0f} m²")
                print(f"   • Max: {s['max']:,.0f} m²")
                print(f"   • Moyenne: {s['moyen']:,.0f} m²")
        
        # 6. Statistiques de loyer
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
            print(f"   • Maisons avec loyer affiché: {s['total']}")
        
        # 7. Répartition par nombre de chambres
        print("\n🛏️ Par nombre de chambres:")
        chambres = collection.aggregate([
            {"$match": {"nombre_chambres": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {"_id": "$nombre_chambres", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ])
        for c in chambres:
            if c['_id']:
                print(f"   • {c['_id']} chambres: {c['count']} maisons")
        
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
        collections_ordre = ['location_appartements', 'vente_appartements', 'vente_villas', 
                           'vente_terrains', 'location_bureaux', 'location_maisons',
                           'vente_maisons', 'location_locaux_commerciaux', 
                           'vente_locaux_commerciaux', 'locationNeuf', 'locations_vacances']
        
        for nom in collections_ordre:
            if nom in collections_info:
                print(f"📍 Collection '{nom}': {collections_info[nom]} documents")
        
        # Afficher les autres collections
        for nom, count in collections_info.items():
            if nom not in collections_ordre:
                print(f"📍 Collection '{nom}': {count} documents")
        
        total_documents = sum(collections_info.values())
        print(f"\n📌 TOTAL GÉNÉRAL: {total_documents} documents dans la base mubaweb")
        
        # Vérification spéciale pour location_maisons
        if 'location_maisons' in collections_info:
            if collections_info['location_maisons'] == 322:
                print("✅ Les 322 locations de maisons ont bien été insérées!")
            else:
                print(f"⚠️ Attention: {collections_info['location_maisons']}/322 maisons insérées")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du récapitulatif: {e}")
    
    # Fermer la connexion
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ Vous pouvez maintenant vérifier vos locations de maisons sur MongoDB Atlas:")
    print("   https://cloud.mongodb.com/ → Collections → EstateMind → Mubaweb.location.Maisons")

if __name__ == "__main__":
    inserer_location_maisons()