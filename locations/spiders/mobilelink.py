# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class MobilelinkSpider(scrapy.Spider):
    name = "mobilelink"
    allowed_domains = ['mobilelinkusa.com']
    start_urls = [
        'https://mobilelinkusa.com/wp-admin/admin-ajax.php?action=store_search&lat=29.760427&lng=-95.36980299999999&max_results=1000&search_radius=10000&autoload=1',
    ]

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for place in data:
            properties = {
                'ref': place["id"],
                'name': place["store"],
                'addr_full': place["address"],
                'city': place["city"],
                'state': place["state"],
                'postcode': place["zip"],
                'country': place["country"],
                'lat': place["lat"],
                'lon': place["lng"],
                'phone': place["phone"],
                'website': place["permalink"]
            }

            yield GeojsonPointItem(**properties)
