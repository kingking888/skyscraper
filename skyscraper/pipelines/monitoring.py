import requests


class PidarMonitoringPipeline(object):
    def __init__(self, pidar_url):
        self.pidar_url = pidar_url

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        return cls(settings.get('PIDAR_URL'))

    def process_item(self, item, spider):
        pidar_alias = '%s-%s' % (item['namespace'], spider.name)
        requests.get('/'.join([self.pidar_url, pidar_alias]))

        return item
