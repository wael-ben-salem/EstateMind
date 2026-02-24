import scrapy

class TunisiapromoVenteItem(scrapy.Item):
    # Identifiants
    annonce_id = scrapy.Field()
    url = scrapy.Field()
    reference = scrapy.Field()
    
    # Informations de base
    titre = scrapy.Field()
    type_offre = scrapy.Field()  # Vente
    type_bien = scrapy.Field()    # Maison, Appartement, Terrain, etc.
    prix = scrapy.Field()
    prix_euro = scrapy.Field()
    
    # Localisation
    region = scrapy.Field()
    ville = scrapy.Field()
    adresse = scrapy.Field()
    code_postal = scrapy.Field()
    
    # Caractéristiques principales
    surface_habitable = scrapy.Field()
    surface_terrain = scrapy.Field()
    pieces = scrapy.Field()
    chambres = scrapy.Field()
    salles_bain = scrapy.Field()
    salles_eau = scrapy.Field()
    places_voiture = scrapy.Field()
    etage = scrapy.Field()
    nombre_etages = scrapy.Field()
    annee_construction = scrapy.Field()
    orientation = scrapy.Field()
    
    # CHAMPS AJOUTÉS
    equipements = scrapy.Field()       # Pour la ligne 268
    etat_bien = scrapy.Field()         # Pour les lignes 308-312
    date_mise_a_jour = scrapy.Field()  # Pour la ligne 358
    
    # Détails
    description = scrapy.Field()
    options = scrapy.Field()
    date_publication = scrapy.Field()
    date_scraping = scrapy.Field()
    
    # Annonceur
    annonceur_nom = scrapy.Field()
    annonceur_type = scrapy.Field()  # Particulier, Agence, Promoteur
    annonceur_telephone = scrapy.Field()
    annonceur_mobile = scrapy.Field()
    annonceur_email = scrapy.Field()
    
    # Média
    images_urls = scrapy.Field()
    video_url = scrapy.Field()
    nombre_photos = scrapy.Field()
    
    # Premium / Stats
    est_premium = scrapy.Field()
    vues = scrapy.Field()
    
    # Métadonnées scraping
    page_trouvee = scrapy.Field()
    statut = scrapy.Field()  # nouveau, existant, modifié