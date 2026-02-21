"""
SCRIPT D'INSERTION ET DE MISE À JOUR DES DONNÉES MENZILI DANS MONGODB ATLAS
Base de données: mubaweb
Collection: menzili_annonces
Fichier: menzili_final.json (27209 annonces)
Fonctionnalité: Insertion intelligente avec détection des nouvelles annonces
"""

import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime
import os
import time

def inserer_ou_mettre_a_jour_menzili():
    print("="*70)
    print("🚀 INSERTION/MISE À JOUR DES ANNONCES MENZILI DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: mubaweb")
    print("📁 Collection: menzili_annonces")
    print("📊 Fichier: menzili_final.json (27209 annonces)")
    print("🔄 Mode: Mise à jour incrémentale (détection des nouvelles annonces)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"
    NOM_COLLECTION = "menzili.vente"
    NOM_FICHIER = "menzili_final.json"
    
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
            print(f"   • Date nettoyage: {metadata.get('date_nettoyage', 'N/A')}")
            print(f"   • Total annonces: {metadata.get('total_annonces', 0)}")
            
            if 'statistiques' in metadata:
                stats = metadata['statistiques']
                print(f"   • Annonces valides: {stats.get('valides', 0)}")
                print(f"   • Annonces invalides: {stats.get('invalides', 0)}")
                print(f"   • Avec téléphone: {stats.get('avec_telephone', 0)}")
                print(f"   • Avec images: {stats.get('avec_images', 0)}")
        
        # Extraire la liste des annonces
        if isinstance(donnees, dict) and 'annonces' in donnees:
            annonces = donnees['annonces']
        elif isinstance(donnees, list):
            annonces = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_annonces = len(annonces)
        print(f"\n✅ {nombre_annonces} annonces trouvées dans le fichier")
        
        # Vérification du nombre attendu
        if nombre_annonces == 27209:
            print("✅ Nombre d'annonces conforme aux métadonnées (27209)")
        else:
            print(f"⚠️ Attention: {nombre_annonces} trouvées, mais les métadonnées indiquent 27209")
        
        # Afficher les types d'annonces
        categories = {}
        for annonce in annonces[:1000]:  # Échantillon pour analyse rapide
            cat = annonce.get('categorie', 'Inconnu')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\n📋 Aperçu des catégories (échantillon):")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {cat}: {count}")
        
        # Afficher un exemple d'annonce
        if nombre_annonces > 0:
            print("\n🔍 Exemple d'annonce Menzili (première du fichier):")
            exemple = annonces[0]
            champs_importants = ['annonce_id', 'titre', 'categorie', 'type_offre', 'ville', 
                                'prix_text', 'surface_habitable', 'chambres', 'est_valide']
            for champ in champs_importants:
                if champ in exemple and exemple[champ] is not None:
                    valeur = exemple[champ]
                    if isinstance(valeur, float) and champ == 'surface_habitable':
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
        
        # Sélectionner la base "mubaweb" et la collection "menzili_annonces"
        db = client[NOM_BASE_DONNEES]
        collection = db[NOM_COLLECTION]
        
        print(f"✅ Base de données '{NOM_BASE_DONNEES}' sélectionnée")
        print(f"✅ Collection '{NOM_COLLECTION}' sélectionnée")
        
        # Vérifier si la collection existe déjà et compter les documents existants
        collections = db.list_collection_names()
        if NOM_COLLECTION in collections:
            ancien_nombre = collection.count_documents({})
            print(f"\n📊 Collection existante: {ancien_nombre} documents déjà présents")
        else:
            print(f"\n📊 Nouvelle collection: Aucun document existant")
            ancien_nombre = 0
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n💡 Vérifiez que:")
        print("   - Votre chaîne de connexion est correcte")
        print("   - Votre IP est autorisée dans MongoDB Atlas")
        return
    
    # 4. Préparer les opérations de mise à jour
    print("\n🔄 Préparation des opérations de mise à jour...")
    
    # Créer un index unique sur annonce_id pour éviter les doublons
    print("   Création de l'index unique sur 'annonce_id'...")
    try:
        collection.create_index("annonce_id", unique=True)
        print("   ✅ Index unique créé sur 'annonce_id'")
    except Exception as e:
        print(f"   ⚠️ Index可能存在: {e}")
    
    # Préparer les opérations bulk
    operations = []
    nouvelles_annonces = 0
    annonces_existantes = 0
    annonces_a_ignorer = 0
    
    # Récupérer tous les IDs existants pour vérification rapide (optionnel)
    ids_existants = set()
    if ancien_nombre > 0:
        print("   Récupération des IDs existants pour optimisation...")
        for doc in collection.find({}, {'annonce_id': 1}):
            if 'annonce_id' in doc:
                ids_existants.add(doc['annonce_id'])
        print(f"   ✅ {len(ids_existants)} IDs récupérés")
    
    debut = time.time()
    
    for i, annonce in enumerate(annonces):
        try:
            # Créer une copie pour ne pas modifier l'original
            doc = annonce.copy()
            
            # Ajouter des métadonnées MongoDB
            doc['_derniere_mise_a_jour'] = datetime.now()
            doc['_source'] = 'menzili'
            
            # S'assurer que l'annonce_id est présent (c'est notre clé unique)
            if 'annonce_id' not in doc:
                doc['annonce_id'] = str(i + 1)
            
            # Vérifier si l'annonce est valide (optionnel)
            est_valide = doc.get('est_valide', True)
            
            # Stratégie: Utiliser update_one avec upsert pour insérer ou ignorer
            # Cela va insérer uniquement les nouvelles annonces
            operations.append(
                UpdateOne(
                    {'annonce_id': doc['annonce_id']},  # Filtre sur l'ID unique
                    {'$set': doc},  # Mettre à jour avec les nouvelles données
                    upsert=True  # Créer si n'existe pas
                )
            )
            
            # Compter les nouvelles vs existantes (approximatif)
            if doc['annonce_id'] in ids_existants:
                annonces_existantes += 1
            else:
                nouvelles_annonces += 1
            
        except Exception as e:
            annonces_a_ignorer += 1
            print(f"   ⚠️ Erreur préparation annonce {i}: {e}")
    
    duree_preparation = time.time() - debut
    
    print(f"\n📊 Résultat de l'analyse:")
    print(f"   • Annonces totales dans le fichier: {len(annonces)}")
    print(f"   • Nouvelles annonces à insérer: {nouvelles_annonces}")
    print(f"   • Annonces déjà existantes: {annonces_existantes}")
    print(f"   • Annonces ignorées (erreurs): {annonces_a_ignorer}")
    
    # 5. Exécuter les opérations bulk
    if operations:
        print(f"\n💾 Exécution des opérations de mise à jour...")
        print(f"   Nombre d'opérations: {len(operations)}")
        
        # Exécuter par lots de 1000 pour éviter les dépassements
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
                print(f"   ✅ Lot {i//batch_size + 1}: {len(batch)} opérations - "
                      f"{resultat.upserted_count} nouvelles, "
                      f"{resultat.modified_count} mises à jour ({pourcentage:.1f}%)")
                
            except Exception as e:
                print(f"   ❌ Erreur lot {i//batch_size + 1}: {e}")
                # Continuer avec le lot suivant
        
        duree_insertion = time.time() - debut_insertion
        
        print(f"\n✅ Opérations terminées en {duree_insertion:.1f} secondes:")
        print(f"   • Nouvelles annonces insérées: {total_insere}")
        print(f"   • Annonces mises à jour: {total_modifie}")
        print(f"   • Total opérations: {len(operations)}")
    else:
        print("\n⚠️ Aucune opération à exécuter")
        total_insere = 0
        total_modifie = 0
    
    # 6. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre total d'annonces dans menzili_annonces: {nombre_final}")
    
    if ancien_nombre > 0:
        evolution = nombre_final - ancien_nombre
        if evolution > 0:
            print(f"✅ Évolution positive: +{evolution} nouvelles annonces")
        elif evolution < 0:
            print(f"⚠️ Attention: {abs(evolution)} annonces ont disparu")
        else:
            print("➡️ Aucun changement dans le nombre d'annonces")
    
    # 7. Créer des index supplémentaires pour optimiser les recherches
    print("\n🔧 Création d'index supplémentaires...")
    try:
        # Index sur les champs fréquemment recherchés
        collection.create_index("categorie")
        print("✅ Index créé sur 'categorie'")
        
        collection.create_index("type_offre")
        print("✅ Index créé sur 'type_offre'")
        
        collection.create_index("ville")
        print("✅ Index créé sur 'ville'")
        
        collection.create_index("region")
        print("✅ Index créé sur 'region'")
        
        collection.create_index("prix")
        print("✅ Index créé sur 'prix'")
        
        collection.create_index("date_publication")
        print("✅ Index créé sur 'date_publication'")
        
        collection.create_index("est_valide")
        print("✅ Index créé sur 'est_valide'")
        
        collection.create_index([("categorie", 1), ("ville", 1)])
        print("✅ Index composé créé (categorie + ville)")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 8. Afficher des statistiques détaillées
    print("\n" + "="*70)
    print("📊 STATISTIQUES DES ANNONCES MENZILI")
    print("="*70)
    
    try:
        # 1. Répartition par catégorie
        print("\n🏷️ Par catégorie:")
        categories = collection.aggregate([
            {"$group": {"_id": "$categorie", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])
        for cat in categories:
            if cat['_id']:
                pourcentage = (cat['count'] / nombre_final) * 100
                print(f"   • {cat['_id']}: {cat['count']} ({pourcentage:.1f}%)")
        
        # 2. Répartition par type d'offre
        print("\n🔄 Par type d'offre:")
        offres = collection.aggregate([
            {"$group": {"_id": "$type_offre", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for offre in offres:
            if offre['_id']:
                pourcentage = (offre['count'] / nombre_final) * 100
                print(f"   • {offre['_id']}: {offre['count']} ({pourcentage:.1f}%)")
        
        # 3. Top 10 villes
        print("\n📍 Top 10 villes:")
        villes = collection.aggregate([
            {"$match": {"ville": {"$ne": "", "$ne": None}}},
            {"$group": {"_id": "$ville", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])
        for ville in villes:
            if ville['_id']:
                print(f"   • {ville['_id']}: {ville['count']} annonces")
        
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
            print(f"\n💰 Prix (TND):")
            print(f"   • Min: {s['min']:,.0f}")
            print(f"   • Max: {s['max']:,.0f}")
            print(f"   • Moyen: {s['moyen']:,.0f}")
            print(f"   • Annonces avec prix: {s['total']}")
        
        # 5. Statistiques de validité
        valides = collection.count_documents({"est_valide": True})
        invalides = collection.count_documents({"est_valide": False})
        print(f"\n✅ Annonces valides: {valides} ({valides/nombre_final*100:.1f}%)")
        print(f"❌ Annonces invalides: {invalides} ({invalides/nombre_final*100:.1f}%)")
        
        # 6. Statistiques de contact
        avec_telephone = collection.count_documents({"telephone": {"$ne": None, "$ne": ""}})
        print(f"📞 Annonces avec téléphone: {avec_telephone} ({avec_telephone/nombre_final*100:.1f}%)")
        
        # 7. Statistiques par année de publication
        print("\n📅 Annonces par année:")
        annees = collection.aggregate([
            {"$match": {"date_publication": {"$ne": None}}},
            {"$group": {
                "_id": {"$year": {"$dateFromString": {"dateString": "$date_publication"}}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 5}
        ])
        for annee in annees:
            if annee['_id']:
                print(f"   • {annee['_id']}: {annee['count']} annonces")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du calcul des statistiques: {e}")
    
    # 9. Récapitulatif final
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF FINAL - MENZILI")
    print("="*70)
    
    print(f"📁 Fichier source: {NOM_FICHIER}")
    print(f"📊 Annonces dans le fichier: {len(annonces)}")
    print(f"📊 Annonces dans la base (avant): {ancien_nombre}")
    print(f"📊 Annonces dans la base (après): {nombre_final}")
    print(f"📈 Nouvelles annonces ajoutées: {total_insere}")
    print(f"🔄 Annonces mises à jour: {total_modifie}")
    
    if ancien_nombre > 0:
        if total_insere > 0:
            print(f"\n✅ Mise à jour réussie: {total_insere} nouvelles annonces ajoutées!")
        else:
            print("\n➡️ Aucune nouvelle annonce détectée. La base est à jour!")
    
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
        collections_ordre = ['menzili_annonces', 'location_appartements', 'vente_appartements', 
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
    print("\n✨ La collection menzili_annonces est prête avec mise à jour automatique!")
    print("   Les prochaines exécutions n'ajouteront que les nouvelles annonces.")
    print("\n👉 Pour automatiser les mises à jour quotidiennes, vous pouvez:")
    print("   1. Créer une tâche planifiée (cron job) qui exécute ce script chaque jour")
    print("   2. Placer le nouveau fichier menzili_final.json dans le même dossier")
    print("   3. Le script détectera automatiquement les nouvelles annonces")

if __name__ == "__main__":
    inserer_ou_mettre_a_jour_menzili()