"""
SCRIPT D'INSERTION DES DONNÉES DANS MONGODB ATLAS
Base de données: EstateMind
Collection: Mubaweb.locations_vacances
"""

import json
from pymongo import MongoClient
from datetime import datetime
import os

def inserer_donnees_mubaweb():
    print("="*60)
    print("🚀 INSERTION DES DONNÉES DANS MONGODB ATLAS")
    print("="*60)
    print("📁 Base de données: EstateMind")
    print("📁 Collection: Mubaweb.locations_vacances")
    print("="*60)
    
    # === CONFIGURATION - À MODIFIER ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"                 # ✅ CHANGÉ
    NOM_COLLECTION = "Mubaweb.locations_vacances"   # ✅ CHANGÉ (prefix Mubaweb.)
    NOM_FICHIER = "listings_propres.json"
    
    # 1. Vérifier que le fichier existe
    if not os.path.exists(NOM_FICHIER):
        print(f"❌ ERREUR: Le fichier {NOM_FICHIER} n'existe pas!")
        print(f"📁 Répertoire courant: {os.getcwd()}")
        return
    
    # 2. Charger les données JSON
    print(f"\n📂 Lecture du fichier: {NOM_FICHIER}")
    try:
        with open(NOM_FICHIER, 'r', encoding='utf-8') as fichier:
            donnees = json.load(fichier)
        
        # Extraire la liste des annonces
        if isinstance(donnees, dict) and 'listings' in donnees:
            annonces = donnees['listings']
        elif isinstance(donnees, list):
            annonces = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_annonces = len(annonces)
        print(f"✅ {nombre_annonces} annonces trouvées dans le fichier")
        
        # Afficher les attributs disponibles (les champs)
        if nombre_annonces > 0:
            print("\n📋 Attributs disponibles dans les données:")
            attributs = list(annonces[0].keys())
            for i, attr in enumerate(attributs, 1):
                print(f"   {i}. {attr}")
        
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
        
        # Sélectionner la base "EstateMind" et la collection "Mubaweb.locations_vacances"
        db = client[NOM_BASE_DONNEES]
        collection = db[NOM_COLLECTION]
        
        print(f"✅ Base de données '{NOM_BASE_DONNEES}' sélectionnée")
        print(f"✅ Collection '{NOM_COLLECTION}' sélectionnée")
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n💡 Vérifiez que:")
        print("   - L'utilisateur/mot de passe sont corrects")
        print("   - Votre IP est autorisée dans MongoDB Atlas (Network Access)")
        print("   - La chaîne de connexion est bien formatée")
        return
    
    # 4. Préparer les documents (conserver tous les attributs originaux)
    print("\n🔄 Préparation des documents...")
    documents = []
    for annonce in annonces:
        # Créer une copie pour ne pas modifier l'original
        doc = annonce.copy()
        
        # Ajouter uniquement des métadonnées (sans modifier les attributs existants)
        doc['date_insertion_mongodb'] = datetime.now()
        
        documents.append(doc)
    
    # 5. VIDER LA COLLECTION (pour éviter les doublons)
    print(f"\n🗑️ Nettoyage de la collection {NOM_COLLECTION}...")
    try:
        resultat_suppression = collection.delete_many({})
        print(f"✅ {resultat_suppression.deleted_count} anciens documents supprimés")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    # 6. CRÉER UN INDEX sur le champ 'id' pour améliorer les recherches
    print("\n🔧 Création des index...")
    try:
        collection.create_index("id", unique=False)  # Unique=False car certains IDs pourraient être null
        print("✅ Index créé sur le champ 'id'")
        
        # Index sur la ville pour les recherches par ville
        collection.create_index("ville")
        print("✅ Index créé sur le champ 'ville'")
        
        # Index sur le prix pour les recherches par prix
        collection.create_index("prix")
        print("✅ Index créé sur le champ 'prix'")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 7. INSÉRER TOUS LES DOCUMENTS
    print(f"\n💾 Insertion de {len(documents)} documents...")
    print("   Attributs préservés: id, titre, url, ville, quartier, prix, ...")
    
    try:
        # Insertion en une seule opération si possible
        resultat = collection.insert_many(documents, ordered=False)
        
        print("\n" + "="*60)
        print("🎉 SUCCÈS! TOUTES LES DONNÉES ONT ÉTÉ INSÉRÉES!")
        print("="*60)
        print(f"📊 Documents insérés: {len(resultat.inserted_ids)} / {len(documents)}")
        print(f"📁 Base de données: {NOM_BASE_DONNEES}")
        print(f"📁 Collection: {NOM_COLLECTION}")
        
    except Exception as e:
        print(f"\n⚠️ Erreur lors de l'insertion massive: {e}")
        print("\n🔄 Tentative d'insertion par lots (plus fiable)...")
        
        try:
            total_insere = 0
            taille_lot = 50  # Lots de 50 documents pour plus de fiabilité
            
            for i in range(0, len(documents), taille_lot):
                lot = documents[i:i+taille_lot]
                try:
                    resultat_lot = collection.insert_many(lot, ordered=False)
                    total_insere += len(resultat_lot.inserted_ids)
                    print(f"   ✅ Lot {i//taille_lot + 1}: {len(resultat_lot.inserted_ids)} insérés")
                except Exception as e_lot:
                    print(f"   ⚠️ Lot {i//taille_lot + 1}: Erreur - insertion un par un...")
                    # Si le lot échoue, essayer document par document
                    for doc in lot:
                        try:
                            collection.insert_one(doc)
                            total_insere += 1
                            print(f"      ✓ Document inséré", end="\r")
                        except Exception as e_doc:
                            print(f"      ✗ Document avec id {doc.get('id', 'inconnu')} non inséré: {str(e_doc)[:50]}")
            
            print(f"\n✅ Total inséré: {total_insere}/{len(documents)} documents")
            
        except Exception as e2:
            print(f"❌ Échec de l'insertion: {e2}")
    
    # 8. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre de documents dans la collection: {nombre_final}")
    
    if nombre_final == len(documents):
        print("✅ SUCCÈS TOTAL: Tous les documents sont présents!")
    else:
        print(f"⚠️ Attention: {nombre_final}/{len(documents)} documents présents")
    
    # 9. Afficher un échantillon des données insérées
    if nombre_final > 0:
        print("\n🔍 Échantillon des données insérées (premier document):")
        premier_doc = collection.find_one()
        if premier_doc:
            print("\n📄 Document exemple avec ses attributs:")
            for key, value in list(premier_doc.items())[:15]:  # Afficher les 15 premiers champs
                if key != '_id':  # Ne pas afficher l'ID MongoDB
                    print(f"   • {key}: {value}")
            if len(premier_doc) > 15:
                print(f"   • ... et {len(premier_doc) - 15} autres attributs")
    
    # 10. Afficher des statistiques
    print("\n📈 Statistiques:")
    try:
        # Compter par ville
        print("   📍 Top 5 villes:")
        villes = collection.aggregate([
            {"$group": {"_id": "$ville", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ])
        for v in villes:
            if v['_id']:  # Ignorer les villes null
                print(f"      • {v['_id']}: {v['count']} annonces")
        
        # Statistiques de prix
        stats_prix = collection.aggregate([
            {"$match": {"prix": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": None,
                "min": {"$min": "$prix"},
                "max": {"$max": "$prix"},
                "moyen": {"$avg": "$prix"},
                "total": {"$sum": 1}
            }}
        ])
        for s in stats_prix:
            print(f"   💰 Prix - Min: {s['min']:.0f} TND, Max: {s['max']:.0f} TND, Moyen: {s['moyen']:.0f} TND")
        
    except Exception as e:
        print(f"   ⚠️ Impossible d'afficher les statistiques: {e}")
    
    # Fermer la connexion
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ Vous pouvez maintenant utiliser vos données dans MongoDB Atlas!")
    print("   Allez sur MongoDB Atlas → Collections → EstateMind → Mubaweb.locations_vacances")

if __name__ == "__main__":
    inserer_donnees_mubaweb()
