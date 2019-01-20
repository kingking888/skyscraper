import scrapy
import datetime

from skyscraper.items import BasicItem
from skyscraper.pipelines.metainfo import AddNamespacePipeline
from skyscraper.pipelines.metainfo import AddSpiderNamePipeline
from skyscraper.pipelines.metainfo import AddCrawlTimePipeline


def test_add_spider_name():
    pipeline = AddSpiderNamePipeline()

    spider = scrapy.Spider(name='my-spider-name')
    item = BasicItem()
    item['id'] = 'my-unique-id'
    item['url'] = 'http://example.com/'
    item['source'] = 'dummy source'
    processed_item = pipeline.process_item(item, spider)

    assert processed_item['spider'] == 'my-spider-name'


def test_add_namespace():
    # TODO: This test should also test from_crawler if possible
    pipeline = AddNamespacePipeline('my-namespace')

    spider = scrapy.Spider(name='my-spider-name')
    item = BasicItem()
    item['id'] = 'my-unique-id'
    item['url'] = 'http://example.com/'
    item['source'] = 'dummy source'
    processed_item = pipeline.process_item(item, spider)

    assert processed_item['namespace'] == 'my-namespace'


def test_add_crawl_time():
    pipeline = AddCrawlTimePipeline()

    spider = scrapy.Spider(name='my-spider-name')
    item = BasicItem()
    item['id'] = 'my-unique-id'
    item['url'] = 'http://example.com/'
    item['source'] = 'dummy source'
    processed_item = pipeline.process_item(item, spider)

    crawl_time = datetime.datetime.strptime(
        processed_item['crawl_time'],
        '%Y-%m-%dT%H:%M:%SZ')

    shortly_ago = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
    shortly_after = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
    assert shortly_ago < crawl_time < shortly_after
