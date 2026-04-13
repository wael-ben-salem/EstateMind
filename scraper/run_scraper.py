from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.tayaraScrapper import TayaraSpider

OUTPUT_FILE = "/opt/spark_app/data/TayaraDataDetailed.json"


def main():
    settings = get_project_settings()
    settings.set("FEEDS", {
        OUTPUT_FILE: {
            "format": "json",
            "overwrite": True,
            "encoding": "utf8",
            "indent": 2,
        }
    })
    settings.set("LOG_LEVEL", "INFO")

    process = CrawlerProcess(settings)
    process.crawl(TayaraSpider)
    process.start()


if __name__ == "__main__":
    main()