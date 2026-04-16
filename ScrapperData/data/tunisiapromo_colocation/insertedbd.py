"""
SCRIPT D'INSERTION ET DE MISE À JOUR DES COLOCATIONS TUNISIE PROMO DANS MONGODB ATLAS
Base de données: mubaweb
Collection: tunisiepromo_colocations
Fichier: colocation_final.json (167 annonces de colocation)
Fonctionnalité: Insertion intelligente avec détection des nouvelles annonces
"""

import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime
import os
import time

def inserer_ou_mettre_a_jour_colocations():
    print("="*70)
    print("🚀 INSERTION/MISE À JOUR DES COLOCATIONS TUNISIE PROMO DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: mubaweb")
    print("📁 Collection: tunisiepromo_colocations")
    print("📊 Fichier: colocation_final.json (167 annonces de colocation)")
    print("🔄 Mode: Mise à jour incrémentale (détection des nouvelles annonces)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"
    NOM_COLLECTION = "tunisiepromo.colocations"
    NOM_FICHIER = "tunisiapromo_final.json"
    
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
        
        # Afficher les métadonnées spécifiques aux colocations
        if 'metadata' in donnees:
            metadata = donnees['metadata']
            print(f"\n📊 MÉTADONNÉES DU FICHIER DE COLOCATIONS:")
            print(f"   • Date nettoyage: {metadata.get('date_nettoyage', 'N/A')}")
            print(f"   • Total annonces colocations: {metadata.get('total_annonces', 0)}")
            
            if 'statistiques' in metadata:
                stats = metadata['statistiques']
                print(f"   • Annonces valides: {stats.get('valides', 0)}")
                print(f"   • Annonces invalides: {stats.get('invalides', 0)}")
                print(f"   • Avec téléphone: {stats.get('avec_telephone', 0)}")
                print(f"   • Offres: {stats.get('offres', 0)}")
                print(f"   • Demandes: {stats.get('demandes', 0)}")
                print(f"   • Recherche femmes: {stats.get('femmes', 0)}")
                print(f"   • Recherche hommes: {stats.get('hommes', 0)}")
        
        # Extraire la liste des annonces de colocation
        if isinstance(donnees, dict) and 'annonces' in donnees:
            annonces = donnees['annonces']
        elif isinstance(donnees, list):
            annonces = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_annonces = len(annonces)
        print(f"\n✅ {nombre_annonces} annonces de colocation trouvées dans le fichier")
        
        # Vérification du nombre attendu
        if nombre_annonces == 167:
            print("✅ Nombre d'annonces conforme aux métadonnées (167)")
        else:
            print(f"⚠️ Attention: {nombre_annonces} trouvées, mais les métadonnées indiquent 167")
        
        # Afficher un exemple d'annonce de colocation
        if nombre_annonces > 0:
            print("\n🔍 Exemple d'annonce de colocation (première du fichier):")
            exemple = annonces[0]
            champs_importants = ['annonce_id', 'titre', 'type_annonce', 'type_bien', 
                                'type_logement', 'prix_text', 'region', 'ville',
                                'genre_recherche', 'profil_recherche', 'nombre_colocataires',
                                'places_voiture', 'est_valide']
            for champ in champs_importants:
                if champ in exemple and exemple[champ] is not None:
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
        # Vérifier la connexion
        client.admin.command('ping')
        print("✅ Connexion réussie!")
        
        # Sélectionner la base "mubaweb" et la collection
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
    print("\n🔄 Préparation des opérations de mise à jour pour les colocations...")
    
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
            doc['_source'] = 'tunisiepromo_colocations'
            doc['_site'] = 'tunisiapromo.com'
            doc['type_offre'] = 'Colocation'
            
            # S'assurer que l'annonce_id est présent
            if 'annonce_id' not in doc:
                doc['annonce_id'] = f"COLO_{i + 1}"
            
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
            
            # Normaliser le type d'annonce
            if 'type_annonce' in doc:
                doc['type_annonce_normalise'] = doc['type_annonce'].lower()
            
            # Normaliser le genre recherché
            if 'genre_recherche' in doc and doc['genre_recherche']:
                genre = doc['genre_recherche'].lower()
                if 'femme' in genre:
                    doc['genre_recherche_normalise'] = 'femme'
                elif 'homme' in genre:
                    doc['genre_recherche_normalise'] = 'homme'
                else:
                    doc['genre_recherche_normalise'] = 'mixte'
            else:
                doc['genre_recherche_normalise'] = 'non spécifié'
            
            # Traiter les listes
            for champ in ['profil_recherche', 'proximites', 'options', 'equipements', 'tous_equipements']:
                if champ in doc and isinstance(doc[champ], list):
                    # Nettoyer les éléments vides
                    doc[champ] = [item for item in doc[champ] if item]
            
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
    
    print(f"\n📊 Résultat de l'analyse des colocations:")
    print(f"   • Annonces dans le fichier: {len(annonces)}")
    print(f"   • Nouvelles à insérer: {nouvelles_annonces}")
    print(f"   • Déjà existantes: {annonces_existantes}")
    print(f"   • Ignorées (erreurs): {annonces_a_ignorer}")
    print(f"   • Temps de préparation: {duree_preparation:.2f} secondes")
    
    # 5. Exécuter les opérations bulk
    if operations:
        print(f"\n💾 Exécution des opérations de mise à jour...")
        print(f"   Nombre d'opérations: {len(operations)}")
        
        batch_size = 100  # Lot plus petit car moins d'annonces
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
        print(f"   • Nouvelles colocations insérées: {total_insere}")
        print(f"   • Colocations mises à jour: {total_modifie}")
        print(f"   • Total opérations: {len(operations)}")
    else:
        print("\n⚠️ Aucune opération à exécuter")
        total_insere = 0
        total_modifie = 0
    
    # 6. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre total de colocations dans la collection: {nombre_final}")
    
    # Statistiques détaillées
    nb_offres = collection.count_documents({"type_annonce_normalise": "offre"})
    nb_demandes = collection.count_documents({"type_annonce_normalise": "demande"})
    nb_femmes = collection.count_documents({"genre_recherche_normalise": "femme"})
    nb_hommes = collection.count_documents({"genre_recherche_normalise": "homme"})
    nb_mixte = collection.count_documents({"genre_recherche_normalise": "mixte"})
    
    print(f"\n📊 Détail après insertion:")
    print(f"   • Offres: {nb_offres}")
    print(f"   • Demandes: {nb_demandes}")
    print(f"   • Recherche femmes: {nb_femmes}")
    print(f"   • Recherche hommes: {nb_hommes}")
    print(f"   • Mixte/non spécifié: {nb_mixte}")
    
    if ancien_nombre > 0:
        evolution = nombre_final - ancien_nombre
        if evolution > 0:
            print(f"\n✅ Évolution positive: +{evolution} nouvelles colocations")
        elif evolution < 0:
            print(f"\n⚠️ Attention: {abs(evolution)} annonces ont disparu")
        else:
            print("\n➡️ Aucun changement")
    
    # 7. Créer des index supplémentaires
    print("\n🔧 Création d'index supplémentaires...")
    try:
        # Index sur les champs fréquemment recherchés
        collection.create_index("type_annonce_normalise")
        print("✅ Index créé sur 'type_annonce_normalise'")
        
        collection.create_index("genre_recherche_normalise")
        print("✅ Index créé sur 'genre_recherche_normalise'")
        
        collection.create_index("region")
        print("✅ Index créé sur 'region'")
        
        collection.create_index("ville")
        print("✅ Index créé sur 'ville'")
        
        collection.create_index("prix")
        print("✅ Index créé sur 'prix'")
        
        collection.create_index("type_bien")
        print("✅ Index créé sur 'type_bien'")
        
        collection.create_index("type_logement")
        print("✅ Index créé sur 'type_logement'")
        
        # Index composés
        collection.create_index([("region", 1), ("prix", 1)])
        print("✅ Index composé créé (region + prix)")
        
        collection.create_index([("genre_recherche_normalise", 1), ("prix", 1)])
        print("✅ Index composé créé (genre + prix)")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 8. Statistiques détaillées
    print("\n" + "="*70)
    print("📊 STATISTIQUES DÉTAILLÉES DES COLOCATIONS")
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
        
        # 2. Répartition par type de bien
        print("\n🏠 Par type de bien:")
        types_bien = collection.aggregate([
            {"$group": {"_id": "$type_bien", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for t in types_bien:
            if t['_id']:
                print(f"   • {t['_id']}: {t['count']}")
        
        # 3. Répartition par type de logement
        print("\n🛏️ Par type de logement:")
        types_logement = collection.aggregate([
            {"$group": {"_id": "$type_logement", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for t in types_logement:
            if t['_id']:
                print(f"   • {t['_id']}: {t['count']}")
        
        # 4. Statistiques de prix
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
        
        # 5. Profils recherchés les plus courants
        print("\n👥 Profils recherchés:")
        profils = collection.aggregate([
            {"$unwind": {"path": "$profil_recherche", "preserveNullAndEmptyArrays": False}},
            {"$group": {"_id": "$profil_recherche", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ])
        for p in profils:
            if p['_id']:
                print(f"   • {p['_id']}: {p['count']} annonces")
        
        # 6. Top villes
        print("\n📍 Top villes:")
        villes = collection.aggregate([
            {"$match": {"ville": {"$ne": "", "$ne": None}}},
            {"$group": {"_id": "$ville", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])
        for v in villes:
            if v['_id']:
                print(f"   • {v['_id']}: {v['count']}")
        
    except Exception as e:
        print(f"⚠️ Erreur lors des statistiques: {e}")
    
    # 9. Récapitulatif final
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF FINAL - COLOCATIONS")
    print("="*70)
    
    print(f"📁 Fichier source: {NOM_FICHIER}")
    print(f"📊 Annonces dans le fichier: {len(annonces)}")
    print(f"📊 Avant insertion: {ancien_nombre}")
    print(f"📊 Après insertion: {nombre_final}")
    print(f"📈 Nouvelles: {total_insere}")
    print(f"🔄 Mises à jour: {total_modifie}")
    
    if total_insere > 0:
        print(f"\n✅ Mise à jour réussie: {total_insere} nouvelles colocations!")
    else:
        print("\n➡️ Aucune nouvelle colocation détectée")
    
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
        collections_ordre = ['menzili_annonces', 'tunisiepromo_colocations', 
                           'location_appartements', 'vente_appartements', 
                           'vente_villas', 'location_villas', 'vente_terrains', 
                           'location_bureaux', 'location_maisons', 'vente_maisons', 
                           'location_locaux_commerciaux', 'vente_locaux_commerciaux', 
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
        
    except Exception as e:
        print(f"⚠️ Erreur lors du récapitulatif: {e}")
    
    # Fermer la connexion
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ La collection tunisiepromo_colocations est maintenant prête!")
    print("   • {} colocations dans la base".format(nombre_final))
    print("\n👉 Les prochaines exécutions n'ajouteront que les nouvelles annonces.")

if __name__ == "__main__":
    inserer_ou_mettre_a_jour_colocations()