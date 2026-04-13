BOT_NAME = 'tunisiapromo_vente'

SPIDER_MODULES = ['tunisiapromo_vente.spiders']
NEWSPIDER_MODULE = 'tunisiapromo_vente.spiders'

ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 1.5
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_DIR = 'httpcache_tunisiapromo'
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 505, 500, 400, 401, 402, 403, 404]

ITEM_PIPELINES = {
    'tunisiapromo_vente.pipelines.TunisiapromoPipeline': 300,
}

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

LOG_LEVEL = 'INFO'