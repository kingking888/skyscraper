import scrapy
import datetime

from skyscraper.items import BasicItem


class IpcheckSpider(scrapy.Spider):
    name = 'ipcheck'
    allowed_domains = ['ipify.org']
    start_urls = ['https://api.ipify.org/']

    def parse(self, response):
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        item = BasicItem()
        item['id'] = 'ipcheck-{}'.format(today)
        item['url'] = response.url
        item['source'] = response.text
        return item
