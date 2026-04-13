import scrapy

class MenziliItem(scrapy.Item):
    # Identifiants
    annonce_id = scrapy.Field()
    url = scrapy.Field()
    
    # Informations de base
    titre = scrapy.Field()
    type_offre = scrapy.Field()  # Acheter/Louer
    categorie = scrapy.Field()    # Appartement, Maison, Terrain, etc.
    prix = scrapy.Field()
    prix_euro = scrapy.Field()
    
    # Localisation
    region = scrapy.Field()
    ville = scrapy.Field()
    adresse_complete = scrapy.Field()
    
    # Caractéristiques principales
    surface_habitable = scrapy.Field()
    surface_terrain = scrapy.Field()
    pieces = scrapy.Field()
    chambres = scrapy.Field()
    salles_bain = scrapy.Field()
    
    # Détails
    description = scrapy.Field()
    options = scrapy.Field()  # Liste des options
    ref_annonce = scrapy.Field()
    date_publication = scrapy.Field()
    
    # Informations vendeur
    vendeur_nom = scrapy.Field()
    vendeur_type = scrapy.Field()  # PRO ou Particulier
    vendeur_telephone = scrapy.Field()
    vendeur_url = scrapy.Field()
    
    # Type d'annonceur (de la liste)
    type_annonceur = scrapy.Field()
    
    # Média
    images_urls = scrapy.Field()
    
    # Premium
    est_premium = scrapy.Field()
    
    # Métadonnées du scraping
    date_scraping = scrapy.Field()
    statut = scrapy.Field()  # nouveau, existant, modifié
    page_trouvee = scrapy.Field()