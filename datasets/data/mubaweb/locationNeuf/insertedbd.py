"""
SCRIPT D'INSERTION DES DONNÉES LOCATIONNEUF DANS MONGODB ATLAS
Base de données: EstateMind
Collection: Mubaweb.locationNeuf
"""

import json
from pymongo import MongoClient
from datetime import datetime
import os

def inserer_locationNeuf():
    print("="*60)
    print("🚀 INSERTION DES DONNÉES LOCATIONNEUF DANS MONGODB ATLAS")
    print("="*60)
    print("📁 Base de données: EstateMind")
    print("📁 Collection: Mubaweb.locationNeuf")
    print("="*60)
    
    # === CONFIGURATION (déjà avec votre chaîne de connexion) ===
    CHAINE_CONNEXION = "mongodb+srv://EstateMindBD:EstateMindBDBD@cluster0.ybul6b0.mongodb.net/?retryWrites=true&w=majority"
    NOM_BASE_DONNEES = "EstateMind"              # ✅ CHANGÉ
    NOM_COLLECTION = "Mubaweb.locationNeuf"      # ✅ CHANGÉ (prefix Mubaweb.)
    NOM_FICHIER = "promotions_final.json"  # À ajuster
    
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
        
        # Extraire la liste des annonces
        if isinstance(donnees, dict) and 'listings' in donnees:
            annonces = donnees['listings']
        elif isinstance(donnees, list):
            annonces = donnees
        else:
            print("❌ Format de fichier non reconnu")
            return
        
        nombre_annonces = len(annonces)
        print(f"✅ {nombre_annonces} annonces de location neuve trouvées dans le fichier")
        
        # Afficher les attributs disponibles
        if nombre_annonces > 0:
            print("\n📋 Attributs disponibles dans les données:")
            attributs = list(annonces[0].keys())
            for i, attr in enumerate(attributs, 1):
                print(f"   {i}. {attr}")
            
            # Afficher un exemple de structure
            print("\n🔍 Exemple de structure de données:")
            exemple = annonces[0]
            for key, value in list(exemple.items())[:10]:
                if isinstance(value, dict):
                    print(f"   • {key}: {type(value).__name__} avec {len(value)} sous-attributs")
                elif isinstance(value, list):
                    print(f"   • {key}: Liste de {len(value)} éléments")
                else:
                    print(f"   • {key}: {value}")
        
    except Exception as e:
        print(f"❌ Erreur de lecture: {e}")
        return
    
    # 3. Connexion à MongoDB Atlas
    print(f"\n🔌 Connexion à MongoDB Atlas...")
    try:
        client = MongoClient(CHAINE_CONNEXION)
        client.admin.command('ping')
        print("✅ Connexion réussie!")
        
        # Sélectionner la base "EstateMind" et la collection "Mubaweb.locationNeuf"
        db = client[NOM_BASE_DONNEES]
        collection = db[NOM_COLLECTION]
        
        print(f"✅ Base de données '{NOM_BASE_DONNEES}' sélectionnée")
        print(f"✅ Collection '{NOM_COLLECTION}' sélectionnée")
        
        # Vérifier si la collection existe déjà
        collections = db.list_collection_names()
        if NOM_COLLECTION in collections:
            print(f"📊 La collection '{NOM_COLLECTION}' existe déjà")
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n💡 Vérifiez que:")
        print("   - Votre chaîne de connexion est correcte")
        print("   - Votre IP est autorisée dans MongoDB Atlas")
        return
    
    # 4. Préparer les documents
    print("\n🔄 Préparation des documents...")
    documents = []
    ids_errors = []
    
    for i, annonce in enumerate(annonces):
        try:
            doc = annonce.copy()
            doc['date_insertion_mongodb'] = datetime.now()
            doc['type_annonce'] = 'location_neuve'
            
            if 'id' not in doc and 'promotion_id' in doc:
                doc['id'] = doc['promotion_id']
            
            documents.append(doc)
            
        except Exception as e:
            ids_errors.append((i, str(e)))
    
    if ids_errors:
        print(f"⚠️ {len(ids_errors)} documents ont eu des erreurs lors de la préparation")
    
    print(f"✅ {len(documents)} documents prêts à être insérés")
    
    # 5. VIDER LA COLLECTION
    print(f"\n🗑️ Nettoyage de la collection {NOM_COLLECTION}...")
    try:
        resultat_suppression = collection.delete_many({})
        print(f"✅ {resultat_suppression.deleted_count} anciens documents supprimés")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    # 6. CRÉER DES INDEX
    print("\n🔧 Création des index...")
    try:
        collection.create_index("id", unique=False)
        print("✅ Index créé sur le champ 'id'")
        
        collection.create_index("ville")
        print("✅ Index créé sur le champ 'ville'")
        
        collection.create_index("prix")
        print("✅ Index créé sur le champ 'prix'")
        
        collection.create_index("type_bien")
        print("✅ Index créé sur le champ 'type_bien'")
        
        collection.create_index("statut_construction.code")
        print("✅ Index créé sur le champ 'statut_construction.code'")
        
    except Exception as e:
        print(f"⚠️ Erreur création index: {e}")
    
    # 7. INSÉRER TOUS LES DOCUMENTS
    print(f"\n💾 Insertion de {len(documents)} documents dans {NOM_COLLECTION}...")
    
    try:
        resultat = collection.insert_many(documents, ordered=False)
        
        print("\n" + "="*60)
        print("🎉 SUCCÈS! TOUTES LES DONNÉES ONT ÉTÉ INSÉRÉES!")
        print("="*60)
        print(f"📊 Documents insérés: {len(resultat.inserted_ids)} / {len(documents)}")
        print(f"📁 Base de données: {NOM_BASE_DONNEES}")
        print(f"📁 Collection: {NOM_COLLECTION}")
        
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
                    print(f"   ✅ Lot {i//taille_lot + 1}: {len(resultat_lot.inserted_ids)} insérés")
                except Exception as e_lot:
                    print(f"   ⚠️ Lot {i//taille_lot + 1}: Insertion individuelle...")
                    for doc in lot:
                        try:
                            collection.insert_one(doc)
                            total_insere += 1
                            print(f"      ✓ {doc.get('id', 'doc')} inséré")
                        except Exception as e_doc:
                            print(f"      ✗ Erreur: {e_doc}")
            
            print(f"\n✅ Total inséré: {total_insere}/{len(documents)} documents")
            
        except Exception as e2:
            print(f"❌ Échec de l'insertion: {e2}")
    
    # 8. Vérification finale
    print("\n🔍 Vérification finale...")
    nombre_final = collection.count_documents({})
    print(f"📊 Nombre de documents dans {NOM_COLLECTION}: {nombre_final}")
    
    if nombre_final == len(documents):
        print("✅ SUCCÈS TOTAL: Tous les documents sont présents!")
    elif nombre_final > 0:
        print(f"⚠️ Partiel: {nombre_final}/{len(documents)} documents présents")
    else:
        print("❌ Aucun document n'a été inséré")
    
    # 9. Afficher un échantillon
    if nombre_final > 0:
        print("\n🔍 Échantillon des données insérées:")
        premier_doc = collection.find_one()
        if premier_doc:
            print("\n📄 Premier document (location neuve):")
            champs_affiches = ['id', 'titre', 'ville', 'prix', 'type_bien', 'statut_construction']
            for champ in champs_affiches:
                if champ in premier_doc:
                    valeur = premier_doc[champ]
                    if isinstance(valeur, dict) and 'label' in valeur:
                        valeur = valeur['label']
                    print(f"   • {champ}: {valeur}")
    
    # 10. Afficher des statistiques
    print("\n📈 Statistiques locationNeuf:")
    try:
        print("   🏢 Types de biens:")
        types = collection.aggregate([
            {"$group": {"_id": "$type_bien", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ])
        for t in types:
            if t['_id']:
                print(f"      • {t['_id']}: {t['count']} annonces")
        
        print("\n   🏗️ Statut de construction:")
        statuts = collection.aggregate([
            {"$group": {"_id": "$statut_construction.label", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        for s in statuts:
            if s['_id']:
                print(f"      • {s['_id']}: {s['count']} annonces")
        
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
            print(f"\n   💰 Prix - Min: {s['min']:,.0f} TND, Max: {s['max']:,.0f} TND, Moyen: {s['moyen']:,.0f} TND")
        
    except Exception as e:
        print(f"   ⚠️ Impossible d'afficher les statistiques: {e}")
    
    # 11. Récapitulatif (avec le préfixe Mubaweb.)
    print("\n" + "="*60)
    print("📊 RÉCAPITULATIF BASE DE DONNÉES EstateMind")
    print("="*60)
    
    try:
        count_neuf = collection.count_documents({})
        print(f"📍 Collection '{NOM_COLLECTION}': {count_neuf} documents")
        
        # Compter dans Mubaweb.locations_vacances (si elle existe)
        collection_vacances = db['Mubaweb.locations_vacances']   # ✅ CHANGÉ
        count_vacances = collection_vacances.count_documents({})
        print(f"📍 Collection 'Mubaweb.locations_vacances': {count_vacances} documents")
        
        print(f"\n📌 TOTAL: {count_neuf + count_vacances} documents dans la base EstateMind")
        
    except Exception as e:
        print(f"⚠️ Erreur lors du récapitulatif: {e}")
    
    client.close()
    print("\n🔒 Connexion fermée")
    print("\n✨ Vérifie sur MongoDB Atlas:")
    print("   Collections → EstateMind → Mubaweb.locationNeuf")

if __name__ == "__main__":
    inserer_locationNeuf()
