import json
import scrapy
from datetime import datetime, timezone


def decode_objectid_timestamp(object_id: str):
    """
    Decode MongoDB ObjectId timestamp from the first 8 hex chars.
    Returns ISO UTC string or None.
    """
    try:
        if not object_id or len(object_id) != 24:
            return None
        ts = int(object_id[:8], 16)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.isoformat()
    except Exception:
        return None


class TayaraSpider(scrapy.Spider):
    name = "tayaradata"
    allowed_domains = ["tayara.tn"]
    api_url = "https://www.tayara.tn/api/marketplace/search-api/"

    LIMIT = 30
    CATEGORY_ID = "60be84bc50ab95b45b08a093"

    def _headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://www.tayara.tn",
            "Referer": "https://www.tayara.tn/listing/c/immobilier/?page=1",
        }

    def start_requests(self):
        payload = {
            "searchRequest": {
                "query": "",
                "offset": 0,
                "limit": self.LIMIT,
                "sort": 0,
                "filter": {
                    "categoryId": self.CATEGORY_ID,
                    "subCategoryId": "",
                    "adParamsMap": {},
                },
                "withPremium": True,
            }
        }

        yield scrapy.Request(
            url=self.api_url,
            method="POST",
            headers=self._headers(),
            body=json.dumps(payload),
            callback=self.parse_api,
            meta={"payload": payload},
        )

    def parse_api(self, response):
        data = response.json()

        try:
            ads = data[0][0]
        except (IndexError, TypeError):
            self.logger.error("Unexpected API structure. Cannot find ads.")
            return

        if not ads:
            self.logger.info("No more ads. Stopping.")
            return

        for ad in ads:
            ad_id = ad.get("id")
            if not ad_id:
                continue

            detail_url = f"https://www.tayara.tn/item/{ad_id}/"

            yield response.follow(
                detail_url,
                callback=self.parse_detail,
                meta={
                    "ad_id": ad_id,
                    "api_title": ad.get("title"),
                    "api_price": ad.get("price"),
                },
            )

        payload = response.meta["payload"].copy()
        payload["searchRequest"] = payload["searchRequest"].copy()
        payload["searchRequest"]["offset"] += payload["searchRequest"]["limit"]

        yield scrapy.Request(
            url=self.api_url,
            method="POST",
            headers=self._headers(),
            body=json.dumps(payload),
            callback=self.parse_api,
            meta={"payload": payload},
        )

    def parse_detail(self, response):
        raw_loc_time = response.xpath(
            ".//div[contains(@class,'space-x-2')][2]/span/text()"
        ).get(default="").strip()

        parts = [p.strip() for p in raw_loc_time.split(",")]
        location = parts[0] if len(parts) > 0 else None
        pub_date = parts[1] if len(parts) > 1 else None

        criteria = [
            t.strip()
            for t in response.css("span.text-gray-700\\/80::text").getall()
            if t.strip()
        ]

        images = response.css("div.carousel img::attr(src)").getall()
        images = list(dict.fromkeys(images))

        ad_id = response.meta.get("ad_id")

        yield {
            "id": ad_id,
            "url": response.url,

            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "published_at_from_id": decode_objectid_timestamp(ad_id),

            "title": response.css("h1.text-gray-700::text").get(default="").strip()
                     or (response.meta.get("api_title") or ""),
            "price": response.css("data::attr(value)").get()
                     or response.meta.get("api_price"),

            "type": response.xpath(
                ".//div[contains(@class,'space-x-2')][1]/span/text()"
            ).get(default="").strip(),

            "location": location,
            "pub_date": pub_date,

            "anouncer": response.css("span.text-gray-700::text").get(default="").strip(),

            "description": " ".join(
                t.strip()
                for t in response.css("p.text-sm span::text").getall()
                if t.strip()
            ),

            "transaction_type": criteria[0] if len(criteria) > 0 else None,
            "superficie": criteria[1] if len(criteria) > 1 else None,
            "nbr_salles_de_bain": criteria[2] if len(criteria) > 2 else None,
            "nbr_chambres": criteria[3] if len(criteria) > 3 else None,

            "phone_number": response.css("a[href^='tel:']::attr(href)").get(default="").replace("tel:", ""),
            "images": images,
        }