import scrapy

class LocationItem(scrapy.Item):
    # Identifiants
    annonce_id = scrapy.Field()
    url = scrapy.Field()
    
    # Informations de base
    titre = scrapy.Field()
    type_offre = scrapy.Field()  # Louer
    categorie = scrapy.Field()    # Appartement, Maison, etc.
    
    # Prix spécial pour location (avec période)
    prix = scrapy.Field()  # Ex: {"montant": 800, "periode": "Mois"}
    prix_euro = scrapy.Field()
    
    # Localisation
    region = scrapy.Field()
    ville = scrapy.Field()
    adresse_complete = scrapy.Field()
    
    # Caractéristiques
    surface_habitable = scrapy.Field()
    surface_terrain = scrapy.Field()
    pieces = scrapy.Field()
    chambres = scrapy.Field()
    salles_bain = scrapy.Field()
    
    # Détails location
    description = scrapy.Field()
    options = scrapy.Field()
    ref_annonce = scrapy.Field()
    date_publication = scrapy.Field()
    type_location = scrapy.Field()  # Annuelle, Saisonnière, Mensuelle
    
    # Vendeur
    vendeur_nom = scrapy.Field()
    vendeur_type = scrapy.Field()
    vendeur_telephone = scrapy.Field()
    vendeur_url = scrapy.Field()
    type_annonceur = scrapy.Field()
    
    # Média
    images_urls = scrapy.Field()
    
    # Premium
    est_premium = scrapy.Field()
    
    # Métadonnées
    date_scraping = scrapy.Field()
    statut = scrapy.Field()
    page_trouvee = scrapy.Field()