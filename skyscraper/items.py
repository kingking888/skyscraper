# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BasicItem(scrapy.Item):
    """BasicItem is the standard item that all spiders have to emit when
    they want to yield a scraped item
    """
    id = scrapy.Field()
    url = scrapy.Field()
    slug = scrapy.Field()  # deprecated
    source = scrapy.Field()
    data = scrapy.Field()
    downloads = scrapy.Field()

    # Automatically filled by pipeline
    crawl_time = scrapy.Field()
    spider = scrapy.Field()
    namespace = scrapy.Field()
