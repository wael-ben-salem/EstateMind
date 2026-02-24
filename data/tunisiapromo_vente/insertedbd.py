"""
SCRIPT D'INSERTION ET DE MISE À JOUR DES VENTES TUNISIE PROMO DANS MONGODB ATLAS
Base de données: mubaweb
Collection: tunisiepromo_ventes
Fichier: vente_final.json (59165 annonces de vente)
Fonctionnalité: Insertion intelligente avec détection des nouvelles annonces
VERSION CORRIGÉE: Gestion robuste des valeurs None
"""

import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime
import os
import time

def inserer_ou_mettre_a_jour_ventes():
    print("="*70)
    print("🚀 INSERTION/MISE À JOUR DES VENTES TUNISIE PROMO DANS MONGODB ATLAS")
    print("="*70)
    print("📁 Base de données: mubaweb")
    print("📁 Collection: tunisiepromo_ventes")
    print("📊 Fichier: vente_final.json (59165 annonces de vente)")
    print("🔄 Mode: Mise à jour incrémentale (détection des nouvelles annonces)")
    print("="*70)
    
    # === CONFIGURATION ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"
    NOM_COLLECTION = "tunisiepromo.ventes"
    NOM_FICHIER = "tunisiapromo_vente_final.json"
    
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
            print(f"\n📊 MÉTADONNÉES DU FICHIER DE VENTES:")
            print(f"   • Date nettoyage: {metadata.get('date_nettoyage', 'N/A')}")
            print(f"   • Total annonces ventes: {metadata.get('total_annonces', 0):,}".replace(',', ' '))
            
            if 'statistiques' in metadata:
                stats = metadata['statistiques']
                print(f"   • Annonces valides: {stats.get('valides', 0):,}".replace(',', ' '))
                print(f"   • Annonces invalides: {stats.get('invalides', 0):,}".replace(',', ' '))
                print(f"   • Avec téléphone: {stats.get('avec_telephone', 0):,}".replace(',', ' '))
                print(f"   • Avec images: {stats.get('avec_images', 0):,}".replace(',', ' '))
                print(f"   • Appartements: {stats.get('appartements', 0):,}".replace(',', ' '))
                print(f"   • Villas: {stats.get('villas', 0):,}".replace(',', ' '))
                print(f"   • Maisons: {stats.get('maisons', 0):,}".replace(',', ' '))
                print(f"   • Terrains: {stats.get('terrains', 0):,}".replace(',', ' '))
                print(f"   • Avec piscine: {stats.get('avec_piscine', 0):,}".replace(',', ' '))
        
        # Extraire la liste des annonces
        if isinstance(donnees, dict) and 'annonces' in donnees:
            annonces = donnees['annonces']
        elif isinstance(donnees, list):
            annonces = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_annonces = len(annonces)
        print(f"\n✅ {nombre_annonces:,} annonces de vente trouvées dans le fichier".replace(',', ' '))
        
        # Vérification du nombre attendu
        if nombre_annonces == 59165:
            print("✅ Nombre d'annonces conforme aux métadonnées (59 165)")
        else:
            print(f"⚠️ Attention: {nombre_annonces} trouvées, mais les métadonnées indiquent 59 165")
        
        # Afficher un exemple
        if nombre_annonces > 0:
            print("\n🔍 Exemple d'annonce de vente (première du fichier):")
            exemple = annonces[0]
            champs_importants = ['annonce_id', 'titre', 'type_bien', 'prix_text', 
                                'region', 'ville', 'surface_habitable', 'surface_terrain',
                                'pieces', 'a_piscine', 'a_jardin', 'titre_foncier', 'est_valide']
            for champ in champs_importants:
                if champ in exemple and exemple[champ] is not None:
                    valeur = exemple[champ]
                    if isinstance(valeur, bool):
                        valeur = "Oui" if valeur else "Non"
                    elif isinstance(valeur, float) and champ in ['surface_habitable', 'surface_terrain']:
                        if valeur:
                            valeur = f"{valeur:,.0f} m²".replace(',', ' ')
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
        print(f"\n📊 Collection existante: {ancien_nombre:,} documents déjà présents".replace(',', ' '))
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n💡 Vérifiez que:")
        print("   - Votre chaîne de connexion est correcte")
        print("   - Votre IP est autorisée dans MongoDB Atlas")
        return
    
    # 4. Préparer les opérations de mise à jour
    print("\n🔄 Préparation des opérations de mise à jour pour les ventes...")
    
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
    print(f"   ✅ {len(ids_existants):,} IDs uniques déjà présents dans la base".replace(',', ' '))
    
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
            doc['_source'] = 'tunisiepromo_ventes'
            doc['_site'] = 'tunisiapromo.com'
            doc['type_offre'] = 'Vente'
            
            # S'assurer que l'annonce_id est présent
            if 'annonce_id' not in doc or not doc['annonce_id']:
                doc['annonce_id'] = f"VENTE_{i + 1}"
            
            # Nettoyer les prix
            if 'prix' in doc and doc['prix'] is not None:
                try:
                    doc['prix'] = float(doc['prix'])
                except (ValueError, TypeError):
                    doc['prix'] = 0
            
            # Calculer prix_m2 si possible
            if 'prix' in doc and doc['prix'] and doc['prix'] > 0:
                surface = doc.get('surface_habitable') or doc.get('surface_terrain')
                if surface and surface > 0:
                    try:
                        doc['prix_m2_calcule'] = round(doc['prix'] / surface, 2)
                    except:
                        pass
            
            # Convertir les types
            if 'surface_habitable' in doc and doc['surface_habitable'] is not None:
                try:
                    doc['surface_habitable'] = float(doc['surface_habitable'])
                except (ValueError, TypeError):
                    doc['surface_habitable'] = None
            
            if 'surface_terrain' in doc and doc['surface_terrain'] is not None:
                try:
                    doc['surface_terrain'] = float(doc['surface_terrain'])
                except (ValueError, TypeError):
                    doc['surface_terrain'] = None
            
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
            
            if 'etage' in doc and doc['etage'] is not None:
                try:
                    doc['etage'] = int(doc['etage'])
                except (ValueError, TypeError):
                    doc['etage'] = None
            
            # Convertir les booléens (gestion des None)
            for champ_bool in ['a_piscine', 'a_jardin', 'a_terrasse', 'a_balcon',
                              'a_climatisation', 'a_chauffage', 'a_securite', 
                              'a_parking', 'cloture', 'a_puit', 'promoteur_direct']:
                if champ_bool in doc and doc[champ_bool] is not None:
                    if isinstance(doc[champ_bool], str):
                        doc[champ_bool] = doc[champ_bool].lower() in ['true', 'oui', '1', 'yes']
                    elif isinstance(doc[champ_bool], (int, float)):
                        doc[champ_bool] = bool(doc[champ_bool])
                elif champ_bool in doc and doc[champ_bool] is None:
                    doc[champ_bool] = False  # Valeur par défaut
            
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
                elif 'terrain' in type_bien_lower:
                    doc['type_bien_normalise'] = 'terrain'
                elif 'ferme' in type_bien_lower:
                    doc['type_bien_normalise'] = 'ferme'
                elif 'local' in type_bien_lower or 'commercial' in type_bien_lower:
                    doc['type_bien_normalise'] = 'local commercial'
                elif 'bureau' in type_bien_lower:
                    doc['type_bien_normalise'] = 'bureau'
                else:
                    doc['type_bien_normalise'] = 'autre'
            else:
                doc['type_bien_normalise'] = 'non spécifié'
            
            # Normaliser le titre foncier
            titre_foncier = doc.get('titre_foncier')
            if titre_foncier is not None and isinstance(titre_foncier, str):
                doc['titre_foncier_normalise'] = titre_foncier.lower()
            else:
                doc['titre_foncier_normalise'] = None
            
            # Traiter les listes
            for champ in ['proximites', 'images']:
                if champ in doc and isinstance(doc[champ], list):
                    doc[champ] = [item for item in doc[champ] if item is not None and item != '']
            
            # Ajouter un champ pour la recherche textuelle (CORRIGÉ)
            texte_parts = []
            for champ_texte in ['titre', 'description', 'ville', 'region']:
                valeur = doc.get(champ_texte, '')
                if valeur is not None:
                    texte_parts.append(str(valeur))
            
            doc['_texte_recherche'] = ' '.join(texte_parts)[:1000] if texte_parts else ''
            
            # Compter le nombre d'images réelles
            if 'images' in doc and isinstance(doc['images'], list):
                doc['nombre_images_reelles'] = len([img for img in doc['images'] 
                                                   if img and 'empty.jpg' not in img])
            else:
                doc['nombre_images_reelles'] = 0
            
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
            
            # Afficher progression tous les 10000 annonces
            if (i + 1) % 10000 == 0:
                print(f"   📊 Progression: {i + 1}/{len(annonces)} annonces préparées")
            
        except Exception as e:
            annonces_a_ignorer += 1
            erreur_msg = f"Annonce {i} (ID: {annonce.get('annonce_id', 'inconnu')}): {str(e)}"
            erreurs_details.append(erreur_msg)
            if annonces_a_ignorer <= 10:
                print(f"   ⚠️ Erreur préparation annonce {i}: {e}")
    
    duree_preparation = time.time() - debut
    
    print(f"\n📊 Résultat de l'analyse des ventes:")
    print(f"   • Annonces dans le fichier: {len(annonces):,}".replace(',', ' '))
    print(f"   • Nouvelles à insérer: {nouvelles_annonces:,}".replace(',', ' '))
    print(f"   • Déjà existantes: {annonces_existantes:,}".replace(',', ' '))
    print(f"   • Ignorées (erreurs): {annonces_a_ignorer:,}".replace(',', ' '))
    print(f"   • Temps de préparation: {duree_preparation:.2f} secondes")
    
    if erreurs_details and len(erreurs_details) > 10:
        print(f"   • {len(erreurs_details)} erreurs au total. Les 10 premières affichées.")
    
    # 5. Exécuter les opérations bulk
    if operations:
        print(f"\n💾 Exécution des opérations de mise à jour...")
        print(f"   Nombre d'opérations: {len(operations):,}".replace(',', ' '))
        
        batch_size = 1000  # Lots de 1000 pour optimiser
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
        print(f"   • Nouvelles ventes insérées: {total_insere:,}".replace(',', ' '))
        print(f"   • Ventes mises à jour: {total_modifie:,}".replace(',', ' '))
        print(f"   • Total opérations: {len(operations):,}".replace(',', ' '))
    else:
        print("\n⚠️ Aucune opération à exécuter")
        total_insere = 0
        total_modifie = 0
    
    # 6. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre total de ventes dans la collection: {nombre_final:,}".replace(',', ' '))
    
    # Statistiques détaillées
    nb_villas = collection.count_documents({"type_bien_normalise": "villa"})
    nb_appartements = collection.count_documents({"type_bien_normalise": "appartement"})
    nb_maisons = collection.count_documents({"type_bien_normalise": "maison"})
    nb_terrains = collection.count_documents({"type_bien_normalise": "terrain"})
    nb_fermes = collection.count_documents({"type_bien_normalise": "ferme"})
    nb_locaux = collection.count_documents({"type_bien_normalise": "local commercial"})
    nb_avec_piscine = collection.count_documents({"a_piscine": True})
    nb_avec_parking = collection.count_documents({"a_parking": True})
    
    print(f"\n📊 Détail par type de bien:")
    print(f"   • Villas: {nb_villas:,}".replace(',', ' '))
    print(f"   • Appartements: {nb_appartements:,}".replace(',', ' '))
    print(f"   • Maisons: {nb_maisons:,}".replace(',', ' '))
    print(f"   • Terrains: {nb_terrains:,}".replace(',', ' '))
    print(f"   • Fermes: {nb_fermes:,}".replace(',', ' '))
    print(f"   • Locaux commerciaux: {nb_locaux:,}".replace(',', ' '))
    print(f"\n🏊 Avec piscine: {nb_avec_piscine:,}".replace(',', ' '))
    print(f"🅿️ Avec parking: {nb_avec_parking:,}".replace(',', ' '))
    
    if ancien_nombre > 0:
        evolution = nombre_final - ancien_nombre
        if evolution > 0:
            print(f"\n✅ Évolution positive: +{evolution:,} nouvelles ventes".replace(',', ' '))
        elif evolution < 0:
            print(f"\n⚠️ Attention: {abs(evolution):,} annonces ont disparu".replace(',', ' '))
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
        
        collection.create_index("surface_terrain")
        print("✅ Index créé sur 'surface_terrain'")
        
        collection.create_index("pieces")
        print("✅ Index créé sur 'pieces'")
        
        collection.create_index("a_piscine")
        print("✅ Index créé sur 'a_piscine'")
        
        collection.create_index("a_parking")
        print("✅ Index créé sur 'a_parking'")
        
        collection.create_index("titre_foncier_normalise")
        print("✅ Index créé sur 'titre_foncier_normalise'")
        
        collection.create_index("est_valide")
        print("✅ Index créé sur 'est_valide'")
        
        # Index composés pour recherches fréquentes
        collection.create_index([("region", 1), ("prix", 1)])
        print("✅ Index composé créé (region + prix)")
        
        collection.create_index([("type_bien_normalise", 1), ("prix", 1)])
        print("✅ Index composé créé (type_bien + prix)")
        
        collection.create_index([("ville", 1), ("type_bien_normalise", 1)])
        print("✅ Index composé créé (ville + type_bien)")
        
        collection.create_index([("region", 1), ("a_piscine", 1)])
        print("✅ Index composé créé (region + a_piscine)")
        
        # Index texte pour recherche full-text
        collection.create_index([("_texte_recherche", "text")])
        print("✅ Index texte créé pour recherche full-text")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 8. Statistiques détaillées
    print("\n" + "="*70)
    print("📊 STATISTIQUES DÉTAILLÉES DES VENTES")
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
                print(f"   • {r['_id']}: {r['count']:,} ({pourcentage:.1f}%)".replace(',', ' '))
        
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
                print(f"   • {v['_id']}: {v['count']:,}".replace(',', ' '))
        
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
            print(f"\n💰 Prix (TND):")
            print(f"   • Min: {s['min']:,.0f}".replace(',', ' '))
            print(f"   • Max: {s['max']:,.0f}".replace(',', ' '))
            print(f"   • Moyen: {s['moyen']:,.0f}".replace(',', ' '))
            print(f"   • Ventes avec prix: {s['total']:,}".replace(',', ' '))
        
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
            print(f"\n📐 Surfaces habitables (m²):")
            print(f"   • Min: {s['min']:,.0f}".replace(',', ' '))
            print(f"   • Max: {s['max']:,.0f}".replace(',', ' '))
            print(f"   • Moyenne: {s['moyen']:,.0f}".replace(',', ' '))
        
        # 5. Équipements les plus courants
        print("\n✨ Équipements:")
        equipements = {
            'Piscine': collection.count_documents({"a_piscine": True}),
            'Jardin': collection.count_documents({"a_jardin": True}),
            'Terrasse': collection.count_documents({"a_terrasse": True}),
            'Parking': collection.count_documents({"a_parking": True}),
            'Climatisation': collection.count_documents({"a_climatisation": True}),
            'Chauffage': collection.count_documents({"a_chauffage": True}),
            'Sécurité': collection.count_documents({"a_securite": True})
        }
        
        for equip, count in sorted(equipements.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                pourcentage = (count / nombre_final) * 100
                print(f"   • {equip}: {count:,} ({pourcentage:.1f}%)".replace(',', ' '))
        
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
                print(f"   • {p['_id']} pièce(s): {p['count']:,}".replace(',', ' '))
        
    except Exception as e:
        print(f"⚠️ Erreur lors des statistiques: {e}")
    
    # 9. Récapitulatif final
    print("\n" + "="*70)
    print("📊 RÉCAPITULATIF FINAL - VENTES TUNISIE PROMO")
    print("="*70)
    
    print(f"📁 Fichier source: {NOM_FICHIER}")
    print(f"📊 Annonces dans le fichier: {len(annonces):,}".replace(',', ' '))
    print(f"📊 Avant insertion: {ancien_nombre:,}".replace(',', ' '))
    print(f"📊 Après insertion: {nombre_final:,}".replace(',', ' '))
    print(f"📈 Nouvelles ventes: {total_insere:,}".replace(',', ' '))
    print(f"🔄 Mises à jour: {total_modifie:,}".replace(',', ' '))
    
    if total_insere > 0:
        print(f"\n✅ Mise à jour réussie: {total_insere:,} nouvelles ventes!".replace(',', ' '))
    else:
        print("\n➡️ Aucune nouvelle vente détectée")
    
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
            'tunisiepromo.ventes',
            'menzili.vente',
            'menzili.location',
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
    print("\n✨ La collection tunisiepromo_ventes est maintenant prête!")
    print(f"   • {nombre_final:,} ventes dans la base".replace(',', ' '))
    print("\n👉 Les prochaines exécutions n'ajouteront que les nouvelles annonces.")

if __name__ == "__main__":
    inserer_ou_mettre_a_jour_ventes()