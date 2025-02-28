# -*- coding: utf-8 -*-
import csv
import scrapy
import json
from locations.items import GeojsonPointItem

HEADERS = {
    'X-Requested-With': 'XMLHttpRequest'
}
STORELOCATOR = 'https://www.starbucks.com/bff/locations?lat={}&lng={}'

class StarbucksSpider(scrapy.Spider):
    name = 'starbucks'
    allowed_domains = ['www.starbucks.com']

    def start_requests(self):
        searchable_point_files = [
            './locations/searchable_points/us_centroids_50mile_radius.csv',
            './locations/searchable_points/ca_centroids_50mile_radius.csv'
        ]

        for point_file in searchable_point_files:
            with open(point_file) as points:
                reader = csv.DictReader(points)
                for point in reader:
                    request = scrapy.Request(
                        url=STORELOCATOR.format(point["latitude"], point["longitude"]),
                        headers=HEADERS,
                        callback=self.parse
                    )
                    # Distance is in degrees...
                    request.meta['distance'] = 1
                    yield request


    def parse(self, response):
        responseJson = json.loads(response.body)
        stores = responseJson['stores']

        for store in stores:
            storeLat = store['coordinates']['latitude']
            storeLon = store['coordinates']['longitude']
            properties = {
                'name': store["name"],
                'addr_full': store['address']['streetAddressLine1'],
                'city': store['address']['city'],
                'state': store['address']['countrySubdivisionCode'],
                'country': store['address']['countryCode'],
                'postcode': store['address']['postalCode'],
                'phone': store['phoneNumber'],
                'ref': store['id'],
                'lon': storeLon,
                'lat': storeLat,
                'extras': {
                    'number': store['storeNumber'],
                    'brand': store['brandName']
                }
            }
            yield GeojsonPointItem(**properties)

        # Get lat and lng from URL
        pairs = response.url.split('?')[-1].split('&')
        # Center is lng, lat
        center = [
            float(pairs[1].split('=')[1]),
            float(pairs[0].split('=')[1])
        ]

        paging = responseJson['paging']
        if paging['returned'] > 0 and paging['limit'] == paging['returned']:
            if response.meta['distance'] > 0.15:
                nextDistance = response.meta['distance'] / 2
                # Create four new coordinate pairs
                nextCoordinates = [
                  [ center[0] - nextDistance, center[1] + nextDistance ],
                  [ center[0] + nextDistance, center[1] + nextDistance ],
                  [ center[0] - nextDistance, center[1] - nextDistance ],
                  [ center[0] + nextDistance, center[1] - nextDistance ]
                ]
                urls = [
                    STORELOCATOR.format(c[1], c[0]) for c in nextCoordinates
                ]
                for url in urls:
                    request = scrapy.Request(
                        url=url,
                        headers=HEADERS,
                        callback=self.parse
                    )
                    request.meta['distance'] = nextDistance
                    yield request
