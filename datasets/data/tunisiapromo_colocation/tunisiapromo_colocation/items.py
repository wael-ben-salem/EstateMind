import scrapy

class TunisiapromoColocationItem(scrapy.Item):
    # Identifiants
    annonce_id = scrapy.Field()
    url = scrapy.Field()
    reference = scrapy.Field()
    
    # Informations de base
    titre = scrapy.Field()
    type_offre = scrapy.Field()  # Colocation
    type_bien = scrapy.Field()    # Appartement, Maison, Bureau, etc.
    type_annonce = scrapy.Field()  # Offre ou Demande
    prix = scrapy.Field()         # Loyer par personne
    prix_euro = scrapy.Field()
    
    # Localisation
    region = scrapy.Field()
    ville = scrapy.Field()
    quartier = scrapy.Field()
    adresse = scrapy.Field()
    code_postal = scrapy.Field()
    
    # Caractéristiques du bien
    surface_habitable = scrapy.Field()
    pieces = scrapy.Field()
    chambres = scrapy.Field()
    salles_bain = scrapy.Field()
    salles_eau = scrapy.Field()
    places_voiture = scrapy.Field()
    etage = scrapy.Field()
    annee_construction = scrapy.Field()
    
    # Détails colocation
    description = scrapy.Field()
    options = scrapy.Field()
    equipements = scrapy.Field()
    date_publication = scrapy.Field()
    date_mise_a_jour = scrapy.Field()
    date_scraping = scrapy.Field()
    genre_recherche = scrapy.Field()  # HF, F, H
    nb_personnes = scrapy.Field()     # Nombre de colocataires cherchés
    total_coloc = scrapy.Field()       # Nombre total de colocataires
    type_logement = scrapy.Field()     # Chambre privée, studio partagé, etc.
    
    # Annonceur
    annonceur_nom = scrapy.Field()
    annonceur_type = scrapy.Field()  # Particulier, Agence
    annonceur_telephone = scrapy.Field()
    annonceur_mobile = scrapy.Field()
    
    # Média
    images_urls = scrapy.Field()
    nombre_photos = scrapy.Field()
    
    # Métadonnées scraping
    page_trouvee = scrapy.Field()
    statut = scrapy.Field()  # nouveau, existant, modifié