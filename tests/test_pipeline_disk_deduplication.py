import pytest
import json
import datetime

from scrapy.spiders import Spider
import scrapy.exceptions
from skyscraper.items import BasicItem
from scrapy.exceptions import DropItem

from skyscraper.pipelines.filesystem import DiskDeduplicationPipeline


class MockDeduplication():
    def __init__(self):
        self.s = set()

    def add_word(self, word):
        self.s.add(word)

    def has_word(self, word):
        return word in self.s


def test_filters_duplicate_item():
    pipeline = DiskDeduplicationPipeline(MockDeduplication(), 'namespace')

    spider = Spider(name='spider')
    item = BasicItem()
    item['id'] = 'my-unique-id'
    item['url'] = 'http://example.com/'
    item['source'] = 'dummy source'

    # one time it should work
    pipeline.process_item(item, spider)

    # afterwards it should throw
    with pytest.raises(DropItem):
        pipeline.process_item(item, spider)

    # for different ID it should work
    item = BasicItem()
    item['id'] = 'my-unique-id-2'
    item['url'] = 'http://example.com/'
    item['source'] = 'dummy source'
    pipeline.process_item(item, spider)
