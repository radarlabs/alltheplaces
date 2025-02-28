# -*- coding: utf-8 -*-
import scrapy
import json


from locations.items import GeojsonPointItem

class RasingCanes(scrapy.Spider):
    name = "raisingcanes"
    allowed_domains = ["www.raisingcanes.com"]
    start_urls = (
        'https://www.raisingcanes.com/locations',
    )

    def start_requests(self):
        base_url = 'https://www.raisingcanes.com/sites/all/themes/raising_cane_s/locator/include/locationsNew.php?&lat={lat}&lng={lng}'

        with open('./locations/searchable_points/us_centroids_100mile_radius.csv') as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(',')
                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        store_data = (data["response"])

        for store in store_data:
            name = store["properties"]["field_alt_title"].strip("&quot;")
            if "Now Open" in name or "Coming Soon" in name:
                continue
            else:
                properties = {
                    'ref': store["properties"]["name"].replace("&#039;s ", " "),
                    'name': name,
                    'addr_full': store["address"],
                    'country': 'US',
                    'lat': float(store["geometry"]["coordinates"][1]),
                    'lon': float(store["geometry"]["coordinates"][0]),
                    'phone': store["properties"]["field_phone"],
                    'website': store["properties"]["path"].strip('<a href="').strip('">Restaurant Details</a>')
                }
                yield GeojsonPointItem(**properties)