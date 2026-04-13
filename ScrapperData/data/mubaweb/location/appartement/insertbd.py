"""
SCRIPT D'INSERTION DES DONNÉES LOCATION APPARTEMENTS DANS MONGODB ATLAS
Base de données: mubaweb
Collection: location_appartements
Fichier: appartement_clear.json (3896 locations d'appartements)
"""

import json
from pymongo import MongoClient
from datetime import datetime
import os
import time

def inserer_location_appartements():
    print("="*70)
    print("🚀 INSERTION DES DONNÉES LOCATION APPARTEMENTS DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: mubaweb")
    print("📁 Collection: location_appartements")
    print("📊 Fichier: appartement_clear.json (3896 locations d'appartements)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"                 
    NOM_COLLECTION = "Mubaweb.location.Appartements" 
    NOM_FICHIER = "appartement_clear.json"
    
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
                    print(f"      • {region}: {stats_region.get('annonces_scrapees', 0)} appartements")
            
            # Afficher les statistiques d'extraction
            if 'statistiques_extraction' in metadata:
                stats_extract = metadata['statistiques_extraction']
                print(f"\n   📊 Statistiques d'extraction:")
                print(f"      • Loyers extraits: {stats_extract.get('loyers_extraits', 0)}")
                print(f"      • Parkings détectés: {stats_extract.get('parkings_detectes', 0)}")
                print(f"      • Ascenseurs détectés: {stats_extract.get('ascenseurs_detectes', 0)}")
                print(f"      • Meublés détectés: {stats_extract.get('meubles_detectes', 0)}")
                print(f"      • Vues mer détectées: {stats_extract.get('vues_mer_detectees', 0)}")
                print(f"      • Terrasses détectées: {stats_extract.get('terrasses_detectees', 0)}")
        
        # Extraire la liste des appartements
        if isinstance(donnees, dict) and 'listings' in donnees:
            appartements = donnees['listings']
        elif isinstance(donnees, list):
            appartements = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_appartements = len(appartements)
        print(f"\n✅ {nombre_appartements} locations d'appartements trouvées dans le fichier")
        
        # Vérification du nombre attendu
        if nombre_appartements == 3896:
            print("✅ Nombre d'appartements conforme aux métadonnées (3896)")
        else:
            print(f"⚠️ Attention: {nombre_appartements} trouvées, mais les métadonnées indiquent 3896")
        
        # Afficher les attributs disponibles
        if nombre_appartements > 0:
            print("\n📋 Attributs spécifiques aux locations d'appartements:")
            attributs_specifiques = ['type_appartement', 'loyer', 'loyer_text', 'loyer_m2', 
                                    'charges_incluses', 'montant_charges', 'caution', 
                                    'duree_location', 'duree_minimum', 'preavis',
                                    'a_ascenseur', 'a_parking', 'meuble', 'a_terrasse', 
                                    'a_balcon', 'cuisine_equipee', 'a_chambre_service',
                                    'animaux_acceptes', 'vue', 'dernier_etage']
            for attr in attributs_specifiques:
                if attr in appartements[0]:
                    print(f"   • {attr}")
            
            # Afficher un exemple d'appartement
            print("\n🔍 Exemple d'appartement à louer (premier du fichier):")
            exemple = appartements[0]
            champs_importants = ['id', 'titre', 'type_appartement', 'ville', 'quartier', 'surface', 
                                'loyer_text', 'duree_location', 'meuble', 'a_terrasse', 'a_balcon',
                                'a_parking', 'vue', 'nombre_pieces', 'nombre_chambres']
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
        
        # Sélectionner la base "mubaweb" et la collection "location_appartements"
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
    
    for i, appartement in enumerate(appartements):
        try:
            # Créer une copie pour ne pas modifier l'original
            doc = appartement.copy()
            
            # Ajouter des métadonnées MongoDB
            doc['_date_insertion'] = datetime.now()
            doc['_type_collection'] = 'location_appartements'
            
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
            
            if 'caution' in doc and doc['caution'] is not None:
                try:
                    doc['caution'] = float(doc['caution'])
                except:
                    pass
            
            # Convertir les booléens
            for champ_bool in ['charges_incluses', 'dernier_etage', 'a_ascenseur', 'a_parking',
                              'meuble', 'a_terrasse', 'a_balcon', 'a_jardin', 'cuisine_equipee',
                              'a_chambre_service', 'a_buanderie', 'a_cellier', 'a_dressing',
                              'a_securite', 'a_internet', 'animaux_acceptes']:
                if champ_bool in doc and doc[champ_bool] is not None:
                    if isinstance(doc[champ_bool], str):
                        doc[champ_bool] = doc[champ_bool].lower() == 'true'
                    elif isinstance(doc[champ_bool], (int, float)):
                        doc[champ_bool] = bool(doc[champ_bool])
            
            # Convertir les entiers
            for champ_int in ['nombre_pieces', 'nombre_chambres', 'nombre_sdb', 'etage', 
                            'nombre_ascenseurs', 'parking_nombre']:
                if champ_int in doc and doc[champ_int] is not None:
                    try:
                        doc[champ_int] = int(doc[champ_int]) if doc[champ_int] != 0 else None
                    except:
                        pass
            
            # Traiter les listes
            for champ in ['equipements', 'proximites']:
                if champ in doc and isinstance(doc[champ], list):
                    # Garder comme liste
                    pass
            
            documents.append(doc)
            
        except Exception as e:
            erreurs.append((i, str(e)))
    
    if erreurs:
        print(f"⚠️ {len(erreurs)} appartements ont eu des erreurs lors de la préparation")
        for err in erreurs[:5]:
            print(f"   • Appartement {err[0]}: {err[1]}")
    
    print(f"✅ {len(documents)} locations d'appartements prêtes à être insérées sur {nombre_appartements}")
    
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
        
        # Index sur le type d'appartement
        collection.create_index("type_appartement")
        print("✅ Index créé sur le champ 'type_appartement'")
        
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
        collection.create_index("meuble")
        print("✅ Index créé sur le champ 'meuble'")
        
        collection.create_index("a_terrasse")
        print("✅ Index créé sur le champ 'a_terrasse'")
        
        collection.create_index("a_balcon")
        print("✅ Index créé sur le champ 'a_balcon'")
        
        collection.create_index("a_parking")
        print("✅ Index créé sur le champ 'a_parking'")
        
        collection.create_index("a_ascenseur")
        print("✅ Index créé sur le champ 'a_ascenseur'")
        
        collection.create_index("vue")
        print("✅ Index créé sur le champ 'vue'")
        
        collection.create_index("duree_location")
        print("✅ Index créé sur le champ 'duree_location'")
        
        # Index géospatial
        if 'localisation' in appartements[0] and 'coordinates' in appartements[0].get('localisation', {}):
            collection.create_index([("localisation.coordinates", "2dsphere")])
            print("✅ Index géospatial créé")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 7. INSÉRER TOUS LES DOCUMENTS (3896 appartements)
    print(f"\n💾 Insertion de {len(documents)} locations d'appartements dans location_appartements...")
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
                print(f"   ✅ Lot {i//taille_lot + 1}: {len(resultat_lot.inserted_ids)} appartements insérés ({pourcentage:.1f}%)")
            except Exception as e_lot:
                print(f"   ⚠️ Lot {i//taille_lot + 1}: Erreur - insertion individuelle...")
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
    
    # 8. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre d'appartements dans location_appartements: {nombre_final}")
    
    if nombre_final == len(documents):
        print("✅ SUCCÈS TOTAL: Tous les appartements à louer sont présents!")
    elif nombre_final > 0:
        pourcentage = (nombre_final / len(documents)) * 100
        print(f"⚠️ Partiel: {nombre_final}/{len(documents)} appartements présents ({pourcentage:.1f}%)")
    else:
        print("❌ Aucun appartement n'a été inséré")
    
    # 9. Afficher un échantillon des données insérées
    if nombre_final > 0:
        print("\n🔍 Échantillon des appartements à louer insérés:")
        appartements_exemples = collection.find().limit(3)
        for i, app in enumerate(appartements_exemples, 1):
            print(f"\n   🏢 Appartement {i}:")
            print(f"      • ID: {app.get('id', 'N/A')}")
            print(f"      • Type: {app.get('type_appartement', 'N/A')}")
            print(f"      • Titre: {app.get('titre', 'N/A')[:60]}...")
            print(f"      • Ville: {app.get('ville', 'N/A')}")
            print(f"      • Quartier: {app.get('quartier', 'N/A')}")
            print(f"      • Surface: {app.get('surface', 'N/A')} m²")
            print(f"      • Loyer: {app.get('loyer_text', 'N/A')}")
            print(f"      • Durée: {app.get('duree_location', 'N/A')}")
            print(f"      • Meublé: {'Oui' if app.get('meuble') else 'Non'}")
            print(f"      • Parking: {'Oui' if app.get('a_parking') else 'Non'}")
            print(f"      • Ascenseur: {'Oui' if app.get('a_ascenseur') else 'Non'}")
            print(f"      • Terrasse: {'Oui' if app.get('a_terrasse') else 'Non'}")
            print(f"      • Balcon: {'Oui' if app.get('a_balcon') else 'Non'}")
            if app.get('vue'):
                print(f"      • Vue: {app.get('vue')}")
            print(f"      • Pièces: {app.get('nombre_pieces', 'N/A')}")
            print(f"      • Chambres: {app.get('nombre_chambres', 'N/A')}")
    
    # 10. Statistiques détaillées
    print("\n" + "="*70)
    print("📊 STATISTIQUES DES LOCATIONS D'APPARTEMENTS")
    print("="*70)
    
    try:
        # 1. Répartition par type d'appartement
        print("\n🏷️ Par type d'appartement:")
        types = collection.aggregate([
            {"$group": {"_id": "$type_appartement", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for t in types:
            if t['_id']:
                print(f"   • {t['_id']}: {t['count']} appartements")
        
        # 2. Répartition par ville
        print("\n📍 Par ville:")
        villes = collection.aggregate([
            {"$group": {"_id": "$ville", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for v in villes:
            if v['_id']:
                print(f"   • {v['_id']}: {v['count']} appartements")
        
        # 3. Répartition par durée de location
        print("\n📅 Par durée de location:")
        durees = collection.aggregate([
            {"$group": {"_id": "$duree_location", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for d in durees:
            if d['_id']:
                print(f"   • {d['_id']}: {d['count']} appartements")
        
        # 4. Statistiques des caractéristiques
        print("\n✨ Caractéristiques:")
        
        # Meublé
        meuble = collection.aggregate([
            {"$match": {"meuble": True}},
            {"$count": "total"}
        ])
        for m in meuble:
            print(f"   • Meublés: {m['total']} appartements ({m['total']/nombre_final*100:.1f}%)")
        
        # Parking
        parking = collection.aggregate([
            {"$match": {"a_parking": True}},
            {"$count": "total"}
        ])
        for p in parking:
            print(f"   • Avec parking: {p['total']} appartements ({p['total']/nombre_final*100:.1f}%)")
        
        # Ascenseur
        ascenseur = collection.aggregate([
            {"$match": {"a_ascenseur": True}},
            {"$count": "total"}
        ])
        for a in ascenseur:
            print(f"   • Avec ascenseur: {a['total']} appartements ({a['total']/nombre_final*100:.1f}%)")
        
        # Terrasse
        terrasse = collection.aggregate([
            {"$match": {"a_terrasse": True}},
            {"$count": "total"}
        ])
        for t in terrasse:
            print(f"   • Avec terrasse: {t['total']} appartements ({t['total']/nombre_final*100:.1f}%)")
        
        # Balcon
        balcon = collection.aggregate([
            {"$match": {"a_balcon": True}},
            {"$count": "total"}
        ])
        for b in balcon:
            print(f"   • Avec balcon: {b['total']} appartements ({b['total']/nombre_final*100:.1f}%)")
        
        # Vue mer
        vue_mer = collection.aggregate([
            {"$match": {"vue": "Mer"}},
            {"$count": "total"}
        ])
        for v in vue_mer:
            print(f"   • Vue sur mer: {v['total']} appartements")
        
        # 5. Statistiques de surface
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
            print(f"   • Appartements avec loyer affiché: {s['total']}")
        
        # 7. Répartition par nombre de pièces
        print("\n🛋️ Par nombre de pièces:")
        pieces = collection.aggregate([
            {"$match": {"nombre_pieces": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {"_id": "$nombre_pieces", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ])
        for p in pieces:
            if p['_id']:
                print(f"   • {p['_id']} pièces: {p['count']} appartements")
        
        # 8. Répartition par nombre de chambres
        print("\n🛏️ Par nombre de chambres:")
        chambres = collection.aggregate([
            {"$match": {"nombre_chambres": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {"_id": "$nombre_chambres", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ])
        for c in chambres:
            if c['_id']:
                print(f"   • {c['_id']} chambres: {c['count']} appartements")
        
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
                           'location_appartements', 'location_locaux_commerciaux', 
                           'locationNeuf', 'locations_vacances']
        
        for nom in collections_ordre:
            if nom in collections_info:
                print(f"📍 Collection '{nom}': {collections_info[nom]} documents")
        
        # Afficher les autres collections
        for nom, count in collections_info.items():
            if nom not in collections_ordre:
                print(f"📍 Collection '{nom}': {count} documents")
        
        total_documents = sum(collections_info.values())
        print(f"\n📌 TOTAL GÉNÉRAL: {total_documents} documents dans la base mubaweb")
        
        # Vérification spéciale pour location_appartements
        if 'location_appartements' in collections_info:
            if collections_info['location_appartements'] == 3896:
                print("✅ Les 3896 locations d'appartements ont bien été insérées!")
            else:
                print(f"⚠️ Attention: {collections_info['location_appartements']}/3896 appartements insérés")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du récapitulatif: {e}")
    
    # Fermer la connexion
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ Vous pouvez maintenant vérifier vos locations d'appartements sur MongoDB Atlas:")
    print("   https://cloud.mongodb.com/ → Collections → EstateMind → Mubaweb.location.Appartements")

if __name__ == "__main__":
    inserer_location_appartements()