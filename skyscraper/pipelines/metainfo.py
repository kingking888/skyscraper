import datetime


class AddCrawlTimePipeline(object):
    def process_item(self, item, spider):
        crawl_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        item['crawl_time'] = crawl_time

        return item


class AddNamespacePipeline(object):
    def __init__(self, namespace):
        self.namespace = namespace

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        namespace = settings.get('USER_NAMESPACE')

        return cls(namespace)

    def process_item(self, item, spider):
        item['namespace'] = self.namespace

        return item


class AddSpiderNamePipeline(object):
    def process_item(self, item, spider):
        item['spider'] = spider.name

        return item
