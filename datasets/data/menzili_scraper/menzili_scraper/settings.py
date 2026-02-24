BOT_NAME = 'menzili_scraper'

SPIDER_MODULES = ['menzili_scraper.spiders']
NEWSPIDER_MODULE = 'menzili_scraper.spiders'

# Obéir au robots.txt
ROBOTSTXT_OBEY = True

# Configuration du téléchargement - OPTIMISÉ POUR 1361 ANNONCES
DOWNLOAD_DELAY = 1.5  # Délai entre les requêtes (respectueux)
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Cache HTTP pour éviter de re-télécharger
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 heures
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 505, 500, 400, 401, 402, 403, 404]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Activer notre pipeline
ITEM_PIPELINES = {
    'menzili_scraper.pipelines.MenziliPipeline': 300,
}

# User Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Télécharger les images (désactivé par défaut)
# IMAGES_STORE = 'images'
# ITEM_PIPELINES['scrapy.pipelines.images.ImagesPipeline'] = 200

# Logging
LOG_LEVEL = 'INFO'
# LOG_FILE = 'scraping.log'  # Décommentez pour sauvegarder les logs