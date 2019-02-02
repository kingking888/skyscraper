import pytest
import os

import scrapy
from scrapy.utils.test import get_crawler

from skyscraper.statscollectors import PostgresStatsCollector


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


def test_statscollector_stores_correct_values(postgresdb):
    spider = scrapy.Spider(name='samplespider')
    crawler = get_crawler(scrapy.Spider, settings_dict={
        'USER_NAMESPACE': 'unit-tests',
        'POSTGRES_CONNSTRING':
            os.environ.get('SKYSCRAPER_UNITTEST_CONNSTRING'),
    })
    stats = PostgresStatsCollector(crawler)

    stats.open_spider(spider)

    stats.inc_value('retry/count')
    stats.inc_value('retry/count')
    stats.inc_value('scheduler/enqueued/disk', count=10)
    stats.inc_value('scheduler/enqueued/memory', count=20)
    stats.inc_value('scheduler/dequeued/disk', count=12)
    stats.inc_value('scheduler/dequeued/memory', count=13)

    stats.close_spider(spider, 'Test End')

    c = postgresdb.cursor()
    c.execute(
        '''SELECT number_of_crawls, requests_retry_count,
            requests_scheduler_enqueued_disk,
            requests_scheduler_enqueued_memory,
            requests_scheduler_dequeued_disk,
            requests_scheduler_dequeued_memory
        FROM skyscraper_spiders_stats_daily
        WHERE spider_id = (
            SELECT spider_id FROM skyscraper_spiders
            WHERE name = 'samplespider'
        )''')
    counters = c.fetchone()

    assert counters[0] == 1
    assert counters[1] == 2
    assert counters[2] == 10
    assert counters[3] == 20
    assert counters[4] == 12
    assert counters[5] == 13


def test_statscollector_can_handle_missing_values(postgresdb):
    spider = scrapy.Spider(name='samplespider')
    crawler = get_crawler(scrapy.Spider, settings_dict={
        'USER_NAMESPACE': 'unit-tests',
        'POSTGRES_CONNSTRING':
            os.environ.get('SKYSCRAPER_UNITTEST_CONNSTRING'),
    })
    stats = PostgresStatsCollector(crawler)

    stats.open_spider(spider)
    # do nothing, so that all keys are missing
    # then we want to see if the stats collector still can handle this
    # situation and set the default values
    stats.close_spider(spider, 'Test End')

    c = postgresdb.cursor()
    c.execute(
        '''SELECT number_of_crawls, requests_retry_count,
            requests_scheduler_enqueued_disk,
            requests_scheduler_enqueued_memory,
            requests_scheduler_dequeued_disk,
            requests_scheduler_dequeued_memory
        FROM skyscraper_spiders_stats_daily
        WHERE spider_id = (
            SELECT spider_id FROM skyscraper_spiders
            WHERE name = 'samplespider'
        )''')
    counters = c.fetchone()

    assert counters[0] == 1
    assert counters[1] == 0
    assert counters[2] == 0
    assert counters[3] == 0
    assert counters[4] == 0
    assert counters[5] == 0
