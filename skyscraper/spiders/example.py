# -*- coding: utf-8 -*-

import scrapy

from skyscraper.items import BasicItem


class ExampleSpider(scrapy.Spider):
    name = 'example'
    allowed_domains = ['example.com']
    start_urls = ['http://example.com/']

    def parse(self, response):
        item = BasicItem()
        item['id'] = 'example.com-indexpage'
        item['url'] = response.url
        item['slug'] = response.url.split('/')[-1]
        item['source'] = response.text
        return item
