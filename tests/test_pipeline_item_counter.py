import datetime

from scrapy.spiders import Spider

from skyscraper.pipelines.postgres import CountItemsPostgresPipeline
from skyscraper.items import BasicItem


def get_spider_item_count(conn, namespace, spider):
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    cursor = conn.cursor()
    cursor.execute('''SELECT items_scraped_count FROM skyscraper_spiders_stats_daily
        WHERE spider_id = (
            SELECT spider_id FROM skyscraper_spiders s
            JOIN projects p ON s.project_id = p.project_id
            WHERE s.name = %s AND p.name = %s
        )
        AND stats_date = %s''', (spider, namespace, today))
    row = cursor.fetchone()
    return row[0]


def test_pipeline_postgres_does_increment(conn):
    pipeline = CountItemsPostgresPipeline(
        conn,
        'test-database')

    spider = Spider(name='test-db-spider')
    item = BasicItem()
    item['id'] = 'my-unique-id'
    item['url'] = 'http://example.com/'
    item['source'] = 'dummy source'

    pipeline.process_item(item, spider)
    count = get_spider_item_count(conn, 'test-database', 'test-db-spider')
    assert count == 1

    pipeline.process_item(item, spider)
    count = get_spider_item_count(conn, 'test-database', 'test-db-spider')
    assert count == 2
