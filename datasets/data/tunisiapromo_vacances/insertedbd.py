"""
SCRIPT D'INSERTION ET DE MISE À JOUR DES LOCATIONS DE VACANCES TUNISIE PROMO DANS MONGODB ATLAS
Base de données: mubaweb
Collection: tunisiepromo_vacances
Fichier: vacances_final.json (69 annonces de locations de vacances)
Fonctionnalité: Insertion intelligente avec détection des nouvelles annonces
VERSION CORRIGÉE: Gestion robuste des valeurs None
"""

import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime
import os
import time

def inserer_ou_mettre_a_jour_vacances():
    print("="*70)
    print("🚀 INSERTION/MISE À JOUR DES LOCATIONS DE VACANCES TUNISIE PROMO DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: mubaweb")
    print("📁 Collection: tunisiepromo_vacances")
    print("📊 Fichier: tunisiapromo_vacances_final.json (69 annonces de locations de vacances)")
    print("🔄 Mode: Mise à jour incrémentale (détection des nouvelles annonces)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"
    NOM_COLLECTION = "tunisiepromo.vacances"
    NOM_FICHIER = "tunisiapromo_vacances_final.json"
    
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
            print(f"\n📊 MÉTADONNÉES DU FICHIER DE VACANCES:")
            print(f"   • Date nettoyage: {metadata.get('date_nettoyage', 'N/A')}")
            print(f"   • Total annonces vacances: {metadata.get('total_annonces', 0)}")
            
            if 'statistiques' in metadata:
                stats = metadata['statistiques']
                print(f"   • Annonces valides: {stats.get('valides', 0)}")
                print(f"   • Annonces invalides: {stats.get('invalides', 0)}")
                print(f"   • Avec téléphone: {stats.get('avec_telephone', 0)}")
                print(f"   • Avec images: {stats.get('avec_images', 0)}")
                print(f"   • Appartements: {stats.get('appartements', 0)}")
                print(f"   • Villas: {stats.get('villas', 0)}")
                print(f"   • Avec piscine: {stats.get('avec_piscine', 0)}")
                print(f"   • Vue mer: {stats.get('vue_mer', 0)}")
        
        # Extraire la liste des annonces
        if isinstance(donnees, dict) and 'annonces' in donnees:
            annonces = donnees['annonces']
        elif isinstance(donnees, list):
            annonces = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_annonces = len(annonces)
        print(f"\n✅ {nombre_annonces} annonces de vacances trouvées dans le fichier")
        
        # Vérification du nombre attendu
        if nombre_annonces == 69:
            print("✅ Nombre d'annonces conforme aux métadonnées (69)")
        else:
            print(f"⚠️ Attention: {nombre_annonces} trouvées, mais les métadonnées indiquent 69")
        
        # Afficher un exemple
        if nombre_annonces > 0:
            print("\n🔍 Exemple d'annonce de vacances (première du fichier):")
            exemple = annonces[0]
            champs_importants = ['annonce_id', 'titre', 'type_bien', 'prix_text', 
                                'region', 'ville', 'capacite', 'surface_habitable',
                                'pieces', 'a_piscine', 'vue', 'distance_mer_m',
                                'proximite_mer', 'periode_disponible', 'est_valide']
            for champ in champs_importants:
                if champ in exemple and exemple[champ] is not None:
                    valeur = exemple[champ]
                    if isinstance(valeur, bool):
                        valeur = "Oui" if valeur else "Non"
                    elif isinstance(valeur, float) and champ in ['surface_habitable', 'distance_mer_m']:
                        if champ == 'distance_mer_m' and valeur:
                            valeur = f"{valeur} m"
                        elif champ == 'surface_habitable' and valeur:
                            valeur = f"{valeur} m²"
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
    print("\n🔄 Préparation des opérations de mise à jour pour les locations de vacances...")
    
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
    erreurs_details = []
    
    debut = time.time()
    
    for i, annonce in enumerate(annonces):
        try:
            # Créer une copie pour ne pas modifier l'original
            doc = annonce.copy()
            
            # Ajouter des métadonnées MongoDB
            doc['_derniere_mise_a_jour'] = datetime.now()
            doc['_source'] = 'tunisiepromo_vacances'
            doc['_site'] = 'tunisiapromo.com'
            doc['type_offre'] = 'Location vacances'
            
            # S'assurer que l'annonce_id est présent
            if 'annonce_id' not in doc or not doc['annonce_id']:
                doc['annonce_id'] = f"VAC_{i + 1}"
            
            # Nettoyer les prix
            if 'prix' in doc and doc['prix'] is not None:
                try:
                    doc['prix'] = float(doc['prix'])
                except (ValueError, TypeError):
                    doc['prix'] = 0
            
            if 'prix_semaine' in doc and doc['prix_semaine'] is not None:
                try:
                    doc['prix_semaine'] = float(doc['prix_semaine'])
                except (ValueError, TypeError):
                    doc['prix_semaine'] = None
            
            if 'prix_jour' in doc and doc['prix_jour'] is not None:
                try:
                    doc['prix_jour'] = float(doc['prix_jour'])
                except (ValueError, TypeError):
                    doc['prix_jour'] = None
            
            # Convertir les types
            if 'surface_habitable' in doc and doc['surface_habitable'] is not None:
                try:
                    doc['surface_habitable'] = float(doc['surface_habitable'])
                except (ValueError, TypeError):
                    doc['surface_habitable'] = None
            
            if 'capacite' in doc and doc['capacite'] is not None:
                try:
                    doc['capacite'] = int(doc['capacite'])
                except (ValueError, TypeError):
                    doc['capacite'] = None
            
            if 'pieces' in doc and doc['pieces'] is not None:
                try:
                    doc['pieces'] = int(doc['pieces'])
                except (ValueError, TypeError):
                    doc['pieces'] = None
            
            if 'chambres' in doc and doc['chambres'] is not None:
                try:
                    doc['chambres'] = int(doc['chambres'])
                except (ValueError, TypeError):
                    doc['chambres'] = None
            
            if 'salles_bain' in doc and doc['salles_bain'] is not None:
                try:
                    doc['salles_bain'] = int(doc['salles_bain'])
                except (ValueError, TypeError):
                    doc['salles_bain'] = None
            
            if 'places_voiture' in doc and doc['places_voiture'] is not None:
                try:
                    doc['places_voiture'] = int(doc['places_voiture'])
                except (ValueError, TypeError):
                    doc['places_voiture'] = None
            
            if 'distance_mer_m' in doc and doc['distance_mer_m'] is not None:
                try:
                    doc['distance_mer_m'] = int(doc['distance_mer_m'])
                except (ValueError, TypeError):
                    doc['distance_mer_m'] = None
            
            if 'etage' in doc and doc['etage'] is not None:
                try:
                    doc['etage'] = int(doc['etage'])
                except (ValueError, TypeError):
                    doc['etage'] = None
            
            # Convertir les booléens (CORRIGÉ - gestion des None)
            for champ_bool in ['a_piscine', 'a_jardin', 'a_terrasse', 'a_balcon',
                              'a_climatisation', 'a_chauffage', 'a_meuble', 
                              'a_cuisine_equipee', 'a_parking', 'a_gardien']:
                if champ_bool in doc and doc[champ_bool] is not None:
                    if isinstance(doc[champ_bool], str):
                        doc[champ_bool] = doc[champ_bool].lower() in ['true', 'oui', '1', 'yes']
                    elif isinstance(doc[champ_bool], (int, float)):
                        doc[champ_bool] = bool(doc[champ_bool])
                elif champ_bool in doc and doc[champ_bool] is None:
                    doc[champ_bool] = False  # Valeur par défaut pour None
            
            # Normaliser le type de bien (CORRIGÉ - gestion des None)
            type_bien = doc.get('type_bien')
            if type_bien is not None and isinstance(type_bien, str):
                type_bien_lower = type_bien.lower()
                if 'villa' in type_bien_lower:
                    doc['type_bien_normalise'] = 'villa'
                elif 'appartement' in type_bien_lower:
                    doc['type_bien_normalise'] = 'appartement'
                elif 'maison' in type_bien_lower:
                    doc['type_bien_normalise'] = 'maison'
                elif 'duplex' in type_bien_lower:
                    doc['type_bien_normalise'] = 'duplex'
                else:
                    doc['type_bien_normalise'] = 'autre'
            else:
                doc['type_bien_normalise'] = 'non spécifié'
            
            # Normaliser la vue (CORRIGÉ - gestion des None)
            vue = doc.get('vue')
            if vue is not None and isinstance(vue, str):
                vue_lower = vue.lower()
                if 'mer' in vue_lower:
                    doc['vue_mer'] = True
                    doc['vue_normalisee'] = 'mer'
                elif 'jardin' in vue_lower:
                    doc['vue_mer'] = False
                    doc['vue_normalisee'] = 'jardin'
                elif 'piscine' in vue_lower:
                    doc['vue_mer'] = False
                    doc['vue_normalisee'] = 'piscine'
                else:
                    doc['vue_mer'] = False
                    doc['vue_normalisee'] = vue_lower
            else:
                doc['vue_mer'] = False
                doc['vue_normalisee'] = None
            
            # Traiter les listes
            for champ in ['proximites', 'options', 'equipements', 'tous_equipements']:
                if champ in doc and isinstance(doc[champ], list):
                    doc[champ] = [item for item in doc[champ] if item is not None and item != '']
            
            # Ajouter un champ pour la recherche textuelle (CORRIGÉ - gestion des None)
            texte_parts = []
            for champ_texte in ['titre', 'description', 'ville', 'region']:
                valeur = doc.get(champ_texte, '')
                if valeur is not None:
                    texte_parts.append(str(valeur))
            
            doc['_texte_recherche'] = ' '.join(texte_parts)[:1000] if texte_parts else ''
            
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
            erreur_msg = f"Annonce {i} (ID: {annonce.get('annonce_id', 'inconnu')}): {str(e)}"
            erreurs_details.append(erreur_msg)
            if annonces_a_ignorer <= 10:  # Afficher seulement les 10 premières erreurs
                print(f"   ⚠️ Erreur préparation annonce {i}: {e}")
    
    duree_preparation = time.time() - debut
    
    print(f"\n📊 Résultat de l'analyse des locations de vacances:")
    print(f"   • Annonces dans le fichier: {len(annonces)}")
    print(f"   • Nouvelles à insérer: {nouvelles_annonces}")
    print(f"   • Déjà existantes: {annonces_existantes}")
    print(f"   • Ignorées (erreurs): {annonces_a_ignorer}")
    print(f"   • Temps de préparation: {duree_preparation:.2f} secondes")
    
    if erreurs_details and len(erreurs_details) > 10:
        print(f"   • {len(erreurs_details)} erreurs au total. Les 10 premières affichées ci-dessus.")
    
    # 5. Exécuter les opérations bulk
    if operations:
        print(f"\n💾 Exécution des opérations de mise à jour...")
        print(f"   Nombre d'opérations: {len(operations)}")
        
        batch_size = 50
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
        print(f"   • Nouvelles locations de vacances insérées: {total_insere}")
        print(f"   • Locations de vacances mises à jour: {total_modifie}")
        print(f"   • Total opérations: {len(operations)}")
    else:
        print("\n⚠️ Aucune opération à exécuter")
        total_insere = 0
        total_modifie = 0
    
    # 6. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre total de locations de vacances dans la collection: {nombre_final}")
    
    # Statistiques détaillées
    nb_villas = collection.count_documents({"type_bien_normalise": "villa"})
    nb_appartements = collection.count_documents({"type_bien_normalise": "appartement"})
    nb_maisons = collection.count_documents({"type_bien_normalise": "maison"})
    nb_duplex = collection.count_documents({"type_bien_normalise": "duplex"})
    nb_avec_piscine = collection.count_documents({"a_piscine": True})
    nb_vue_mer = collection.count_documents({"vue_mer": True})
    
    print(f"\n📊 Détail par type de bien:")
    print(f"   • Villas: {nb_villas}")
    print(f"   • Appartements: {nb_appartements}")
    print(f"   • Maisons: {nb_maisons}")
    print(f"   • Duplex: {nb_duplex}")
    print(f"\n🏊 Avec piscine: {nb_avec_piscine}")
    print(f"🌊 Vue mer: {nb_vue_mer}")
    
    if ancien_nombre > 0:
        evolution = nombre_final - ancien_nombre
        if evolution > 0:
            print(f"\n✅ Évolution positive: +{evolution} nouvelles locations de vacances")
        elif evolution < 0:
            print(f"\n⚠️ Attention: {abs(evolution)} annonces ont disparu")
        else:
            print("\n➡️ Aucun changement")
    
    # 7. Créer des index supplémentaires
    print("\n🔧 Création d'index supplémentaires...")
    try:
        # Index sur les champs spécifiques aux vacances
        collection.create_index("type_bien_normalise")
        print("✅ Index créé sur 'type_bien_normalise'")
        
        collection.create_index("region")
        print("✅ Index créé sur 'region'")
        
        collection.create_index("ville")
        print("✅ Index créé sur 'ville'")
        
        collection.create_index("prix")
        print("✅ Index créé sur 'prix'")
        
        collection.create_index("prix_semaine")
        print("✅ Index créé sur 'prix_semaine'")
        
        collection.create_index("prix_jour")
        print("✅ Index créé sur 'prix_jour'")
        
        collection.create_index("capacite")
        print("✅ Index créé sur 'capacite'")
        
        collection.create_index("a_piscine")
        print("✅ Index créé sur 'a_piscine'")
        
        collection.create_index("vue_mer")
        print("✅ Index créé sur 'vue_mer'")
        
        collection.create_index("periode_disponible")
        print("✅ Index créé sur 'periode_disponible'")
        
        # Index composés pour recherches fréquentes
        collection.create_index([("region", 1), ("a_piscine", 1)])
        print("✅ Index composé créé (region + a_piscine)")
        
        collection.create_index([("ville", 1), ("prix_jour", 1)])
        print("✅ Index composé créé (ville + prix_jour)")
        
        collection.create_index([("type_bien_normalise", 1), ("capacite", 1)])
        print("✅ Index composé créé (type_bien + capacite)")
        
        # Index texte pour recherche full-text
        collection.create_index([("_texte_recherche", "text")])
        print("✅ Index texte créé pour recherche full-text")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 8. Statistiques détaillées
    print("\n" + "="*70)
    print("📊 STATISTIQUES DÉTAILLÉES DES LOCATIONS DE VACANCES")
    print("="*70)
    
    try:
        # 1. Répartition par région
        print("\n📍 Par région:")
        regions = collection.aggregate([
            {"$group": {"_id": "$region", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for r in regions:
            if r['_id']:
                pourcentage = (r['count'] / nombre_final) * 100
                print(f"   • {r['_id']}: {r['count']} ({pourcentage:.1f}%)")
        
        # 2. Top villes
        print("\n📍 Top villes:")
        villes = collection.aggregate([
            {"$match": {"ville": {"$ne": "", "$ne": None}}},
            {"$group": {"_id": "$ville", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ])
        for v in villes:
            if v['_id']:
                print(f"   • {v['_id']}: {v['count']}")
        
        # 3. Statistiques de capacité
        stats_capacite = collection.aggregate([
            {"$match": {"capacite": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$capacite"},
                "max": {"$max": "$capacite"},
                "moyen": {"$avg": "$capacite"},
                "total": {"$sum": 1}
            }}
        ])
        for s in stats_capacite:
            print(f"\n👥 Capacité:")
            print(f"   • Min: {s['min']} personnes")
            print(f"   • Max: {s['max']} personnes")
            print(f"   • Moyenne: {s['moyen']:.1f} personnes")
        
        # 4. Statistiques des prix journaliers
        stats_prix_jour = collection.aggregate([
            {"$match": {"prix_jour": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$prix_jour"},
                "max": {"$max": "$prix_jour"},
                "moyen": {"$avg": "$prix_jour"},
                "total": {"$sum": 1}
            }}
        ])
        for s in stats_prix_jour:
            print(f"\n💰 Prix par jour (TND):")
            print(f"   • Min: {s['min']:,.0f}")
            print(f"   • Max: {s['max']:,.0f}")
            print(f"   • Moyen: {s['moyen']:,.0f}")
        
        # 5. Statistiques des prix semaine
        stats_prix_semaine = collection.aggregate([
            {"$match": {"prix_semaine": {"$exists": True, "$ne": None, "$ne": 0}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$prix_semaine"},
                "max": {"$max": "$prix_semaine"},
                "moyen": {"$avg": "$prix_semaine"},
                "total": {"$sum": 1}
            }}
        ])
        for s in stats_prix_semaine:
            print(f"\n💰 Prix par semaine (TND):")
            print(f"   • Min: {s['min']:,.0f}")
            print(f"   • Max: {s['max']:,.0f}")
            print(f"   • Moyen: {s['moyen']:,.0f}")
        
        # 6. Équipements les plus courants
        print("\n✨ Équipements:")
        equipements = {
            'Piscine': collection.count_documents({"a_piscine": True}),
            'Jardin': collection.count_documents({"a_jardin": True}),
            'Terrasse': collection.count_documents({"a_terrasse": True}),
            'Climatisation': collection.count_documents({"a_climatisation": True}),
            'Chauffage': collection.count_documents({"a_chauffage": True}),
            'Parking': collection.count_documents({"a_parking": True}),
            'Vue mer': collection.count_documents({"vue_mer": True})
        }
        
        for equip, count in sorted(equipements.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                pourcentage = (count / nombre_final) * 100
                print(f"   • {equip}: {count} ({pourcentage:.1f}%)")
        
        # 7. Répartition par période de disponibilité
        print("\n📅 Par période:")
        periodes = collection.aggregate([
            {"$group": {"_id": "$periode_disponible", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for p in periodes:
            if p['_id']:
                print(f"   • {p['_id']}: {p['count']}")
        
        # 8. Proximité mer
        print("\n🌊 Proximité mer:")
        tres_proche = collection.count_documents({"distance_mer_m": {"$lte": 100}})
        proche = collection.count_documents({"distance_mer_m": {"$gt": 100, "$lte": 500}})
        print(f"   • À moins de 100m: {tres_proche}")
        print(f"   • Entre 100m et 500m: {proche}")
        
    except Exception as e:
        print(f"⚠️ Erreur lors des statistiques: {e}")
    
    # 9. Récapitulatif final
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF FINAL - LOCATIONS DE VACANCES")
    print("="*70)
    
    print(f"📁 Fichier source: {NOM_FICHIER}")
    print(f"📊 Annonces dans le fichier: {len(annonces)}")
    print(f"📊 Avant insertion: {ancien_nombre}")
    print(f"📊 Après insertion: {nombre_final}")
    print(f"📈 Nouvelles locations de vacances: {total_insere}")
    print(f"🔄 Mises à jour: {total_modifie}")
    
    if total_insere > 0:
        print(f"\n✅ Mise à jour réussie: {total_insere} nouvelles locations de vacances!")
    else:
        print("\n➡️ Aucune nouvelle location de vacances détectée")
    
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
            'tunisiepromo.locations',
            'tunisiepromo.vacances',
            'tunisiepromo.colocations',
            'Mubaweb.location.Appartements',
            'Mubaweb.vente.Appartements',
            'Mubaweb.vente.Villas',
            'Mubaweb.location.Villas',
            'Mubaweb.vente.Terrain',
            'Mubaweb.location.Bureaux',
            'Mubaweb.location.Maisons',
            'Mubaweb.vente.Maisons',
            'Mubaweb.location.LocauxCommerciaux',
            'Mubaweb.vente.LocauxCommerciaux',
            'Mubaweb.locationNeuf',
            'Mubaweb.locations_vacances'
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
    print("\n✨ La collection tunisiepromo_vacances est maintenant prête!")
    print(f"   • {nombre_final} locations de vacances dans la base")
    print("\n👉 Les prochaines exécutions n'ajouteront que les nouvelles annonces.")

if __name__ == "__main__":
    inserer_ou_mettre_a_jour_vacances()