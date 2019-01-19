import pytest
import mock

import scrapy
from scrapy.statscollectors import StatsCollector
from scrapy.utils.test import get_crawler

import uuid
import datetime

from skyscraper.scheduler import PostgresScheduler


@pytest.fixture
def postgresdb(conn):
    code = '''import scrapy
class MySpider(scrapy.Spider):
    name = 'samplespider'
    '''

    c = conn.cursor()
    c.execute("INSERT INTO projects (name) VALUES ('unit-tests')")
    c.execute(
        """INSERT INTO skyscraper_spiders
        (name, project_id, code, recurrency_minutes)
        VALUES (
            'samplespider',
            (SELECT project_id FROM projects WHERE name = 'unit-tests'),
            %s,
            60)""",
        (code,))
    conn.commit()

    yield conn

    c.execute(
        '''DELETE FROM skyscraper_spiders
        WHERE project_id = (
            SELECT project_id FROM projects
            WHERE name = 'unit-tests'
        )''')
    c.execute("""DELETE FROM projects
        WHERE name = 'unit-tests'""")
    conn.commit()


def build_always_false_dupefilter():
    dupefilter = mock.Mock()
    dupefilter.request_seen.return_value = False

    return dupefilter


def test_scheduler_does_keep_k_requests_in_memory(postgresdb):
    spider = scrapy.Spider(name='samplespider')
    crawler = get_crawler(scrapy.Spider)
    stats = StatsCollector(crawler)

    dupefilter = build_always_false_dupefilter()
    scheduler = PostgresScheduler(dupefilter, postgresdb, stats,
                                  'unit-tests', 10)
    scheduler.open(spider)

    requests = [
        'https://example.com/',
        'https://example.com/subsite',
        'https://example.com/another-subsite',
    ]
    for request in requests:
        scheduler.enqueue_request(scrapy.Request(request))

    counter = 0
    while scheduler.next_request():
        counter += 1

    assert counter == 3


def test_scheduler_does_offload_after_k_elements(postgresdb):
    spider = scrapy.Spider(name='samplespider')
    crawler = get_crawler(scrapy.Spider)
    stats = StatsCollector(crawler)

    dupefilter = build_always_false_dupefilter()
    scheduler = PostgresScheduler(dupefilter, postgresdb, stats,
                                  'unit-tests', 2)
    scheduler.open(spider)

    requests = [
        'https://example.com/',
        'https://example.com/subsite',
        'https://example.com/another-subsite',
        'https://example.com/yet-another-subsite',
    ]
    for request in requests:
        scheduler.enqueue_request(scrapy.Request(request))

    counter = 0
    while scheduler.next_request():
        counter += 1

    assert counter == 2

    c = postgresdb.cursor()
    c.execute(
        '''SELECT COUNT(*) FROM skyscraper_requests
        WHERE spider_id = (
            SELECT spider_id FROM skyscraper_spiders
            WHERE name = 'samplespider'
        )''')
    counter_in_db = c.fetchone()[0]
    assert counter_in_db == 2


def test_scheduler_does_continue_backlog(postgresdb):
    num_process_items = 3

    # Fill database
    backlog_requests = [
        'https://example.com/',
        'https://example.com/subsite',
        'https://example.com/another-subsite',
        'https://example.com/yet-another-subsite',
    ]
    c = postgresdb.cursor()
    for request in backlog_requests:
        request_id = str(uuid.uuid4())
        c.execute('''INSERT INTO skyscraper_requests
            (request_id, spider_id, priority, url, method, create_date)
            VALUES
            (
                %s,
                (SELECT spider_id FROM skyscraper_spiders
                WHERE name = 'samplespider'),
                0,
                %s,
                'GET',
                %s
            )''', (request_id, request, datetime.datetime.utcnow()))
    postgresdb.commit()

    # Run scheduler
    spider = scrapy.Spider(name='samplespider')
    crawler = get_crawler(scrapy.Spider)
    stats = StatsCollector(crawler)

    dupefilter = build_always_false_dupefilter()
    scheduler = PostgresScheduler(dupefilter, postgresdb, stats,
                                  'unit-tests', num_process_items)
    scheduler.open(spider)

    counter = 0
    while scheduler.next_request():
        counter += 1

    assert counter == num_process_items

    # Database must be empty now
    c = postgresdb.cursor()
    c.execute(
        '''SELECT COUNT(*) FROM skyscraper_requests
        WHERE spider_id = (
            SELECT spider_id FROM skyscraper_spiders
            WHERE name = 'samplespider'
        )''')
    counter_in_db = c.fetchone()[0]
    assert counter_in_db == len(backlog_requests) - num_process_items


def test_can_handle_bytes_in_headers(postgresdb):
    spider = scrapy.Spider(name='samplespider')
    crawler = get_crawler(scrapy.Spider)
    stats = StatsCollector(crawler)

    dupefilter = build_always_false_dupefilter()
    scheduler = PostgresScheduler(dupefilter, postgresdb, stats,
                                  'unit-tests', 0)
    scheduler.open(spider)

    headers = {b'Referer': [b'https://example.org/']}
    request = scrapy.Request('https://example.com/', headers=headers)

    scheduler.enqueue_request(request)

    c = postgresdb.cursor()
    c.execute(
        '''SELECT COUNT(*) FROM skyscraper_requests
        WHERE spider_id = (
            SELECT spider_id FROM skyscraper_spiders
            WHERE name = 'samplespider'
        )''')
    counter_in_db = c.fetchone()[0]
    assert counter_in_db == 1


def test_can_serialize_and_deserialize_callbacks(postgresdb):
    class TestSpider(scrapy.Spider):
        def my_method(self, response):
            pass

        def my_err_method(self, response):
            pass

    spider = TestSpider(name='samplespider')
    crawler = get_crawler(scrapy.Spider)
    stats = StatsCollector(crawler)

    dupefilter = build_always_false_dupefilter()
    scheduler = PostgresScheduler(dupefilter, postgresdb, stats,
                                  'unit-tests', 0)
    scheduler.open(spider)

    callback = spider.my_method
    errback = spider.my_err_method
    request = scrapy.Request('https://example.com/',
                             callback=callback,
                             errback=errback)

    scheduler.enqueue_request(request)

    c = postgresdb.cursor()
    c.execute(
        '''SELECT callback, errback FROM skyscraper_requests
        WHERE spider_id = (
            SELECT spider_id FROM skyscraper_spiders
            WHERE name = 'samplespider'
        )''')
    entry_in_db = c.fetchone()
    assert entry_in_db[0] == 'self.my_method'
    assert entry_in_db[1] == 'self.my_err_method'

    scheduler = PostgresScheduler(dupefilter, postgresdb, stats,
                                  'unit-tests', 1)
    scheduler.open(spider)

    req_from_db = scheduler.next_request()
    assert req_from_db.callback == spider.my_method
    assert req_from_db.errback == spider.my_err_method
