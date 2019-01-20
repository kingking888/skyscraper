# -*- coding: utf-8 -*-

import logging
import json
import datetime

import psycopg2
import uuid

from scrapy.exporters import PythonItemExporter


class CountItemsPostgresPipeline(object):
    def __init__(self, conn, namespace):
        self.conn = conn
        self.namespace = namespace

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        connstring = settings.get('POSTGRES_CONNSTRING')
        namespace = settings.get('USER_NAMESPACE')

        conn = psycopg2.connect(connstring)

        return cls(conn, namespace)

    def process_item(self, item, spider):
        # If there already is a crawl_time for the item, use the existing
        # one to avoid logging the wrong date when an item was crawled at
        # 23:59:59, but this pipeline is only triggered at 00:00:00 the
        # next day
        if 'crawl_time' in item:
            today = item['crawl_time'][0:10]
        else:
            today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

        spider.log('Incrementing item count for %s/%s'
                   % (self.namespace, spider.name),
                   logging.DEBUG)

        c = self.conn.cursor()
        c.execute('''INSERT INTO skyscraper_spiders_stats_daily AS stats_daily
            (spider_id, stats_date, items_scraped_count)
            VALUES (
                (SELECT spider_id FROM skyscraper_spiders s
                    JOIN projects p ON s.project_id = p.project_id
                    WHERE s.name = %s AND p.name = %s),
                %s,
                1)
            ON CONFLICT (spider_id, stats_date) DO UPDATE
                SET items_scraped_count = stats_daily.items_scraped_count + 1''',
            (spider.name,
                self.namespace,
                today))

        self.conn.commit()

        return item


class SaveDataToPostgresPipeline(object):
    def __init__(self, conn, namespace):
        self.conn = conn
        self.namespace = namespace

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        connstring = settings.get('POSTGRES_CONNSTRING')
        namespace = settings.get('USER_NAMESPACE')

        conn = psycopg2.connect(connstring)

        return cls(conn, namespace)

    def process_item(self, item, spider):
        ie = self._get_exporter()
        exported = ie.export_item(item)
        payload = json.dumps(exported)

        c = self.conn.cursor()
        c.execute('''INSERT INTO skyscraper_spiders_results
            (item_id, spider_id, payload, crawl_date)
            VALUES (
                %s,
                (SELECT spider_id FROM skyscraper_spiders s
                    JOIN projects p ON s.project_id = p.project_id
                    WHERE s.name = %s AND p.name = %s),
                %s,
                %s)''',
            (str(uuid.uuid4()),
                spider.name,
                self.namespace,
                payload,
                crawl_time))

        self.conn.commit()

        return item

    def _get_exporter(self, **kwargs):
        return PythonItemExporter(binary=False, **kwargs)
