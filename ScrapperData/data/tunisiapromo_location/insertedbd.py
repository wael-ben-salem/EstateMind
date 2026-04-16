"""
SCRIPT D'INSERTION ET DE MISE À JOUR DES LOCATIONS TUNISIE PROMO DANS MONGODB ATLAS
Base de données: mubaweb
Collection: tunisiepromo_locations
Fichier: location_final.json (24414 annonces de location)
Fonctionnalité: Insertion intelligente avec détection des nouvelles annonces
"""

import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime
import os
import time

def inserer_ou_mettre_a_jour_locations():
    print("="*70)
    print("🚀 INSERTION/MISE À JOUR DES LOCATIONS TUNISIE PROMO DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: mubaweb")
    print("📁 Collection: tunisiepromo_locations")
    print("📊 Fichier: location_final.json (24414 annonces de location)")
    print("🔄 Mode: Mise à jour incrémentale (détection des nouvelles annonces)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"
    NOM_COLLECTION = "tunisiepromo.locations"
    NOM_FICHIER = "tunisiapromo_location_final.json"
    
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
            print(f"\n📊 MÉTADONNÉES DU FICHIER DE LOCATIONS:")
            print(f"   • Date nettoyage: {metadata.get('date_nettoyage', 'N/A')}")
            print(f"   • Total annonces locations: {metadata.get('total_annonces', 0)}")
            
            if 'statistiques' in metadata:
                stats = metadata['statistiques']
                print(f"   • Annonces valides: {stats.get('valides', 0)}")
                print(f"   • Annonces invalides: {stats.get('invalides', 0)}")
                print(f"   • Avec téléphone: {stats.get('avec_telephone', 0)}")
                print(f"   • Avec images: {stats.get('avec_images', 0)}")
                print(f"   • Appartements: {stats.get('appartements', 0)}")
                print(f"   • Maisons: {stats.get('maisons', 0)}")
                print(f"   • Locations annuelles: {stats.get('location_annuelle', 0)}")
        
        # Extraire la liste des annonces
        if isinstance(donnees, dict) and 'annonces' in donnees:
            annonces = donnees['annonces']
        elif isinstance(donnees, list):
            annonces = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_annonces = len(annonces)
        print(f"\n✅ {nombre_annonces} annonces de location trouvées dans le fichier")
        
        # Vérification du nombre attendu
        if nombre_annonces == 24414:
            print("✅ Nombre d'annonces conforme aux métadonnées (24414)")
        else:
            print(f"⚠️ Attention: {nombre_annonces} trouvées, mais les métadonnées indiquent 24414")
        
        # Afficher un exemple
        if nombre_annonces > 0:
            print("\n🔍 Exemple d'annonce de location (première du fichier):")
            exemple = annonces[0]
            champs_importants = ['annonce_id', 'titre', 'type_bien', 'prix_text', 
                                'region', 'ville', 'type_location', 'surface_habitable',
                                'pieces', 'a_piscine', 'a_jardin', 'a_climatisation',
                                'a_chauffage', 'a_parking', 'est_valide']
            for champ in champs_importants:
                if champ in exemple and exemple[champ] is not None:
                    valeur = exemple[champ]
                    if isinstance(valeur, bool):
                        valeur = "Oui" if valeur else "Non"
                    elif isinstance(valeur, float) and champ == 'surface_habitable':
                        valeur = f"{valeur} m²"
                    elif champ == 'prix_text':
                        pass  # Garder tel quel
                    print(f"   • {champ}: {valeur}")
            
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
        
        # Sélectionner la base et la collection
        db = client[NOM_BASE_DONNEES]
        collection = db[NOM_COLLECTION]
        
        print(f"✅ Base de données '{NOM_BASE_DONNEES}' sélectionnée")
        print(f"✅ Collection '{NOM_COLLECTION}' sélectionnée")
        
        # Vérifier le nombre de documents existants
        ancien_nombre = collection.count_documents({})
        print(f"\n📊 Collection existante: {ancien_nombre} documents déjà présents")
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n💡 Vérifiez que:")
        print("   - Votre chaîne de connexion est correcte")
        print("   - Votre IP est autorisée dans MongoDB Atlas")
        return
    
    # 4. Préparer les opérations de mise à jour
    print("\n🔄 Préparation des opérations de mise à jour pour les locations...")
    
    # Créer un index unique sur annonce_id
    print("   Vérification de l'index unique sur 'annonce_id'...")
    try:
        collection.create_index("annonce_id", unique=True)
        print("   ✅ Index unique créé/vérifié sur 'annonce_id'")
    except Exception as e:
        print(f"   ⚠️ Note: {e}")
    
    # Récupérer tous les IDs existants pour optimisation
    print("   Récupération des IDs existants pour optimisation...")
    ids_existants = set()
    for doc in collection.find({}, {'annonce_id': 1}):
        if 'annonce_id' in doc:
            ids_existants.add(doc['annonce_id'])
    print(f"   ✅ {len(ids_existants)} IDs uniques déjà présents dans la base")
    
    # Préparer les opérations bulk
    operations = []
    nouvelles_annonces = 0
    annonces_existantes = 0
    annonces_a_ignorer = 0
    
    debut = time.time()
    
    for i, annonce in enumerate(annonces):
        try:
            # Créer une copie pour ne pas modifier l'original
            doc = annonce.copy()
            
            # Ajouter des métadonnées MongoDB
            doc['_derniere_mise_a_jour'] = datetime.now()
            doc['_source'] = 'tunisiepromo_locations'
            doc['_site'] = 'tunisiapromo.com'
            doc['type_offre'] = 'Location'  # Déjà présent mais on le force
            
            # S'assurer que l'annonce_id est présent
            if 'annonce_id' not in doc:
                doc['annonce_id'] = f"LOC_{i + 1}"
            
            # Nettoyer le prix
            if 'prix' in doc and doc['prix'] is not None:
                try:
                    doc['prix'] = float(doc['prix'])
                except:
                    doc['prix'] = 0
            
            # Convertir les types
            if 'surface_habitable' in doc and doc['surface_habitable'] is not None:
                try:
                    doc['surface_habitable'] = float(doc['surface_habitable'])
                except:
                    doc['surface_habitable'] = None
            
            if 'pieces' in doc and doc['pieces'] is not None:
                try:
                    doc['pieces'] = int(doc['pieces'])
                except:
                    doc['pieces'] = None
            
            if 'etage' in doc and doc['etage'] is not None:
                try:
                    doc['etage'] = int(doc['etage'])
                except:
                    doc['etage'] = None
            
            if 'parking_nombre' in doc and doc['parking_nombre'] is not None:
                try:
                    doc['parking_nombre'] = int(doc['parking_nombre'])
                except:
                    doc['parking_nombre'] = None
            
            # Convertir les booléens
            for champ_bool in ['dernier_etage', 'a_piscine', 'a_jardin', 'a_ascenseur',
                              'a_gardien', 'a_terrasse', 'a_balcon', 'a_climatisation',
                              'a_chauffage', 'a_meuble', 'a_cuisine_equipee', 'a_parking']:
                if champ_bool in doc and doc[champ_bool] is not None:
                    if isinstance(doc[champ_bool], str):
                        doc[champ_bool] = doc[champ_bool].lower() == 'true'
                    elif isinstance(doc[champ_bool], (int, float)):
                        doc[champ_bool] = bool(doc[champ_bool])
            
            # Normaliser le type de bien
            type_bien = doc.get('type_bien', '').lower()
            if 'appartement' in type_bien:
                doc['type_bien_normalise'] = 'appartement'
            elif 'maison' in type_bien:
                doc['type_bien_normalise'] = 'maison'
            elif 'villa' in type_bien:
                doc['type_bien_normalise'] = 'villa'
            elif 'studio' in type_bien:
                doc['type_bien_normalise'] = 'studio'
            elif 'bureau' in type_bien:
                doc['type_bien_normalise'] = 'bureau'
            elif 'local' in type_bien:
                doc['type_bien_normalise'] = 'local commercial'
            else:
                doc['type_bien_normalise'] = 'autre'
            
            # Traiter les listes
            for champ in ['proximites', 'options', 'equipements', 'tous_equipements']:
                if champ in doc and isinstance(doc[champ], list):
                    doc[champ] = [item for item in doc[champ] if item]
            
            # Ajouter un champ pour la recherche textuelle
            doc['_texte_recherche'] = ' '.join([
                doc.get('titre', ''),
                doc.get('description', ''),
                doc.get('ville', ''),
                doc.get('region', '')
            ])[:1000]  # Limiter à 1000 caractères
            
            # Vérifier si l'annonce est valide
            est_valide = doc.get('est_valide', True)
            
            # Stratégie: Utiliser update_one avec upsert
            operations.append(
                UpdateOne(
                    {'annonce_id': doc['annonce_id']},
                    {'$set': doc},
                    upsert=True
                )
            )
            
            # Compter les nouvelles vs existantes
            if doc['annonce_id'] in ids_existants:
                annonces_existantes += 1
            else:
                nouvelles_annonces += 1
            
        except Exception as e:
            annonces_a_ignorer += 1
            if annonces_a_ignorer < 10:
                print(f"   ⚠️ Erreur préparation annonce {i}: {e}")
    
    duree_preparation = time.time() - debut
    
    print(f"\n📊 Résultat de l'analyse des locations:")
    print(f"   • Annonces dans le fichier: {len(annonces)}")
    print(f"   • Nouvelles à insérer: {nouvelles_annonces}")
    print(f"   • Déjà existantes: {annonces_existantes}")
    print(f"   • Ignorées (erreurs): {annonces_a_ignorer}")
    print(f"   • Temps de préparation: {duree_preparation:.2f} secondes")
    
    # 5. Exécuter les opérations bulk
    if operations:
        print(f"\n💾 Exécution des opérations de mise à jour...")
        print(f"   Nombre d'opérations: {len(operations)}")
        
        batch_size = 1000
        total_insere = 0
        total_modifie = 0
        
        debut_insertion = time.time()
        
        for i in range(0, len(operations), batch_size):
            batch = operations[i:i+batch_size]
            try:
                resultat = collection.bulk_write(batch, ordered=False)
                total_insere += resultat.upserted_count
                total_modifie += resultat.modified_count
                
                pourcentage = (min(i+batch_size, len(operations)) / len(operations)) * 100
                print(f"   ✅ Lot {i//batch_size + 1}: {len(batch)} annonces - "
                      f"{resultat.upserted_count} nouvelles, "
                      f"{resultat.modified_count} mises à jour ({pourcentage:.1f}%)")
                
            except Exception as e:
                print(f"   ❌ Erreur lot {i//batch_size + 1}: {e}")
        
        duree_insertion = time.time() - debut_insertion
        
        print(f"\n✅ Opérations terminées en {duree_insertion:.1f} secondes:")
        print(f"   • Nouvelles locations insérées: {total_insere}")
        print(f"   • Locations mises à jour: {total_modifie}")
        print(f"   • Total opérations: {len(operations)}")
    else:
        print("\n⚠️ Aucune opération à exécuter")
        total_insere = 0
        total_modifie = 0
    
    # 6. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre total de locations dans la collection: {nombre_final}")
    
    # Statistiques détaillées
    nb_appartements = collection.count_documents({"type_bien_normalise": "appartement"})
    nb_maisons = collection.count_documents({"type_bien_normalise": "maison"})
    nb_villas = collection.count_documents({"type_bien_normalise": "villa"})
    nb_studios = collection.count_documents({"type_bien_normalise": "studio"})
    nb_bureaux = collection.count_documents({"type_bien_normalise": "bureau"})
    nb_locaux = collection.count_documents({"type_bien_normalise": "local commercial"})
    
    print(f"\n📊 Détail par type de bien:")
    print(f"   • Appartements: {nb_appartements}")
    print(f"   • Maisons: {nb_maisons}")
    print(f"   • Villas: {nb_villas}")
    print(f"   • Studios: {nb_studios}")
    print(f"   • Bureaux: {nb_bureaux}")
    print(f"   • Locaux commerciaux: {nb_locaux}")
    
    if ancien_nombre > 0:
        evolution = nombre_final - ancien_nombre
        if evolution > 0:
            print(f"\n✅ Évolution positive: +{evolution} nouvelles locations")
        elif evolution < 0:
            print(f"\n⚠️ Attention: {abs(evolution)} annonces ont disparu")
        else:
            print("\n➡️ Aucun changement")
    
    # 7. Créer des index supplémentaires
    print("\n🔧 Création d'index supplémentaires...")
    try:
        # Index sur les champs fréquemment recherchés
        collection.create_index("type_bien_normalise")
        print("✅ Index créé sur 'type_bien_normalise'")
        
        collection.create_index("region")
        print("✅ Index créé sur 'region'")
        
        collection.create_index("ville")
        print("✅ Index créé sur 'ville'")
        
        collection.create_index("prix")
        print("✅ Index créé sur 'prix'")
        
        collection.create_index("surface_habitable")
        print("✅ Index créé sur 'surface_habitable'")
        
        collection.create_index("pieces")
        print("✅ Index créé sur 'pieces'")
        
        collection.create_index("a_piscine")
        print("✅ Index créé sur 'a_piscine'")
        
        collection.create_index("a_jardin")
        print("✅ Index créé sur 'a_jardin'")
        
        collection.create_index("a_climatisation")
        print("✅ Index créé sur 'a_climatisation'")
        
        collection.create_index("a_chauffage")
        print("✅ Index créé sur 'a_chauffage'")
        
        collection.create_index("a_parking")
        print("✅ Index créé sur 'a_parking'")
        
        collection.create_index("a_meuble")
        print("✅ Index créé sur 'a_meuble'")
        
        # Index composés pour recherches fréquentes
        collection.create_index([("region", 1), ("prix", 1)])
        print("✅ Index composé créé (region + prix)")
        
        collection.create_index([("type_bien_normalise", 1), ("prix", 1)])
        print("✅ Index composé créé (type_bien + prix)")
        
        collection.create_index([("ville", 1), ("type_bien_normalise", 1)])
        print("✅ Index composé créé (ville + type_bien)")
        
        # Index texte pour recherche full-text
        collection.create_index([("_texte_recherche", "text")])
        print("✅ Index texte créé pour recherche full-text")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 8. Statistiques détaillées
    print("\n" + "="*70)
    print("📊 STATISTIQUES DÉTAILLÉES DES LOCATIONS")
    print("="*70)
    
    try:
        # 1. Répartition par région
        print("\n📍 Par région:")
        regions = collection.aggregate([
            {"$group": {"_id": "$region", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])
        for r in regions:
            if r['_id']:
                pourcentage = (r['count'] / nombre_final) * 100
                print(f"   • {r['_id']}: {r['count']} ({pourcentage:.1f}%)")
        
        # 2. Top villes
        print("\n📍 Top 10 villes:")
        villes = collection.aggregate([
            {"$match": {"ville": {"$ne": "", "$ne": None}}},
            {"$group": {"_id": "$ville", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])
        for v in villes:
            if v['_id']:
                print(f"   • {v['_id']}: {v['count']}")
        
        # 3. Statistiques de prix
        stats_prix = collection.aggregate([
            {"$match": {"prix": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$prix"},
                "max": {"$max": "$prix"},
                "moyen": {"$avg": "$prix"},
                "total": {"$sum": 1}
            }}
        ])
        for s in stats_prix:
            print(f"\n💰 Prix (TND/mois):")
            print(f"   • Min: {s['min']:,.0f}")
            print(f"   • Max: {s['max']:,.0f}")
            print(f"   • Moyen: {s['moyen']:,.0f}")
            print(f"   • Locations avec prix: {s['total']}")
        
        # 4. Statistiques de surface
        stats_surface = collection.aggregate([
            {"$match": {"surface_habitable": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$surface_habitable"},
                "max": {"$max": "$surface_habitable"},
                "moyen": {"$avg": "$surface_habitable"},
                "total": {"$sum": 1}
            }}
        ])
        for s in stats_surface:
            print(f"\n📐 Surfaces:")
            print(f"   • Min: {s['min']:,.0f} m²")
            print(f"   • Max: {s['max']:,.0f} m²")
            print(f"   • Moyenne: {s['moyen']:,.0f} m²")
        
        # 5. Équipements les plus courants
        print("\n✨ Équipements:")
        equipements = {
            'Climatisation': collection.count_documents({"a_climatisation": True}),
            'Chauffage': collection.count_documents({"a_chauffage": True}),
            'Parking': collection.count_documents({"a_parking": True}),
            'Jardin': collection.count_documents({"a_jardin": True}),
            'Piscine': collection.count_documents({"a_piscine": True}),
            'Meublé': collection.count_documents({"a_meuble": True}),
            'Ascenseur': collection.count_documents({"a_ascenseur": True}),
            'Balcon': collection.count_documents({"a_balcon": True}),
            'Terrasse': collection.count_documents({"a_terrasse": True})
        }
        
        for equip, count in sorted(equipements.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                pourcentage = (count / nombre_final) * 100
                print(f"   • {equip}: {count} ({pourcentage:.1f}%)")
        
        # 6. Répartition par nombre de pièces
        print("\n🛋️ Par nombre de pièces:")
        pieces_stats = collection.aggregate([
            {"$match": {"pieces": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {"_id": "$pieces", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
            {"$limit": 10}
        ])
        for p in pieces_stats:
            if p['_id']:
                print(f"   • {p['_id']} pièce(s): {p['count']}")
        
    except Exception as e:
        print(f"⚠️ Erreur lors des statistiques: {e}")
    
    # 9. Récapitulatif final
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF FINAL - LOCATIONS TUNISIE PROMO")
    print("="*70)
    
    print(f"📁 Fichier source: {NOM_FICHIER}")
    print(f"📊 Annonces dans le fichier: {len(annonces)}")
    print(f"📊 Avant insertion: {ancien_nombre}")
    print(f"📊 Après insertion: {nombre_final}")
    print(f"📈 Nouvelles locations: {total_insere}")
    print(f"🔄 Mises à jour: {total_modifie}")
    
    if total_insere > 0:
        print(f"\n✅ Mise à jour réussie: {total_insere} nouvelles locations!")
    else:
        print("\n➡️ Aucune nouvelle location détectée")
    
    # 10. Récapitulatif de toutes les collections
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF BASE DE DONNÉES mubaweb")
    print("="*70)
    
    try:
        collections_info = {}
        for nom_collection in db.list_collection_names():
            count = db[nom_collection].count_documents({})
            collections_info[nom_collection] = count
        
        # Afficher dans un ordre spécifique
        collections_ordre = [
            'menzili_annonces',
            'tunisiepromo_locations',
            'tunisiepromo_colocations',
            'location_appartements',
            'vente_appartements',
            'vente_villas',
            'location_villas',
            'vente_terrains',
            'location_bureaux',
            'location_maisons',
            'vente_maisons',
            'location_locaux_commerciaux',
            'vente_locaux_commerciaux',
            'locationNeuf',
            'locations_vacances'
        ]
        
        for nom in collections_ordre:
            if nom in collections_info:
                print(f"📍 Collection '{nom}': {collections_info[nom]:,} documents".replace(',', ' '))
        
        # Afficher les autres collections
        for nom, count in collections_info.items():
            if nom not in collections_ordre:
                print(f"📍 Collection '{nom}': {count:,} documents".replace(',', ' '))
        
        total_documents = sum(collections_info.values())
        print(f"\n📌 TOTAL GÉNÉRAL: {total_documents:,} documents dans la base mubaweb".replace(',', ' '))
        
    except Exception as e:
        print(f"⚠️ Erreur lors du récapitulatif: {e}")
    
    # Fermer la connexion
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ La collection tunisiepromo_locations est maintenant prête!")
    print(f"   • {nombre_final:,} locations dans la base".replace(',', ' '))
    print("\n👉 Les prochaines exécutions n'ajouteront que les nouvelles annonces.")

if __name__ == "__main__":
    inserer_ou_mettre_a_jour_locations()