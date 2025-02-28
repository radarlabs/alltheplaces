# -*- coding: utf-8 -*-
import scrapy
import json
import traceback
import re
from locations.items import GeojsonPointItem


class TacobellSpider(scrapy.Spider):
    name = "tacobell"
    allowed_domains = ["locations.tacobell.com"]
    start_urls = ("https://locations.tacobell.com/",)
    download_delay = 0.2

    def normalize_hours(self, hours):

        all_days = []
        reversed_hours = {}

        for hour in json.loads(hours):
            all_intervals = []
            short_day = hour['day'].title()[:2]

            if not hour['intervals']:
                continue

            for interval in hour['intervals']:
                start = str(interval['start']).zfill(4)
                end = str(interval['end']).zfill(4)
                from_hr = "{}:{}".format(start[:2],
                                         start[2:]
                                         )
                to_hr = "{}:{}".format(end[:2],
                                       end[2:]
                                       )
                epoch = '{}-{}'.format(from_hr, to_hr)
                all_intervals.append(epoch)
            reversed_hours.setdefault(', '.join(all_intervals), [])
            reversed_hours[epoch].append(short_day)

        if len(reversed_hours) == 1 and list(reversed_hours)[0] == '00:00-24:00':
            return '24/7'
        opening_hours = []

        for key, value in reversed_hours.items():
            if len(value) == 1:
                opening_hours.append('{} {}'.format(value[0], key))
            else:
                opening_hours.append(
                    '{}-{} {}'.format(value[0], value[-1], key))
        return "; ".join(opening_hours)

    def parse_location(self, response):

        hours = response.xpath('//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days').extract_first()
        opening_hours = self.normalize_hours(hours)

        props = {
            'addr_full': response.xpath('//span[@itemprop="streetAddress"]/span/text()').extract_first().strip(),
            'lat': float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
            'lon': float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            'city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            'state': response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            'phone': response.xpath('//span[@class="c-phone-number-span c-phone-main-number-span"]/text()').extract_first(),
            'ref': response.xpath('//div[@class="nap-content main"]/@data-code').extract_first(),
            'website': response.url,
            'opening_hours': opening_hours,
        }

        return GeojsonPointItem(**props)

    def parse_city_stores(self, response):
        locations = response.xpath('//a[@class="c-location-grid-item-link"]/@href').extract()

        if not locations:
            yield self.parse_location(response)
        else:
            for location in locations:
                yield scrapy.Request(
                    url=response.urljoin(location),
                    callback=self.parse_location
                )

    def parse_state(self, response):
        cities = response.xpath('//li[@class="c-directory-list-content-item"]/a/@href').extract()
        for city in cities:
            yield scrapy.Request(
                response.urljoin(city),
                callback=self.parse_city_stores
            )

    def parse(self, response):
        states = response.xpath('//li[@class="c-directory-list-content-item"]/a/@href').extract()

        for state in states:
            yield scrapy.Request(
                response.urljoin(state),
                callback=self.parse_state
            )
