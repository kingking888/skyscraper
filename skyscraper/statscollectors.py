import psycopg2
import datetime

from scrapy.statscollectors import StatsCollector


class PostgresStatsCollector(StatsCollector):
    def __init__(self, crawler):
        super(PostgresStatsCollector, self).__init__(crawler)

        settings = crawler.settings
        connstring = settings.get('POSTGRES_CONNSTRING')
        self.conn = psycopg2.connect(connstring)

        self.namespace = settings.get('USER_NAMESPACE')

    def _persist_stats(self, stats, spider):
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

        # The assumption regarding number_of_crawls here is that
        # _persist_stats is only called when the spider closes the stats
        # collector and that the spider only closes the stats collector
        # when it is finished with crawling.
        # If this assumption does not hold true, it is incorrect to increment
        # the number_of_crawls by 1 here
        c = self.conn.cursor()
        c.execute('''INSERT INTO skyscraper_spiders_stats_daily AS stats_daily
            (spider_id, stats_date, number_of_crawls, requests_retry_count,
                requests_scheduler_enqueued_disk,
                requests_scheduler_enqueued_memory,
                requests_scheduler_dequeued_disk,
                requests_scheduler_dequeued_memory)
            VALUES (
                (SELECT spider_id FROM skyscraper_spiders s
                    JOIN projects p ON s.project_id = p.project_id
                    WHERE s.name = %s AND p.name = %s),
                %s, 1, %s, %s, %s, %s, %s)
            ON CONFLICT (spider_id, stats_date) DO UPDATE
                SET number_of_crawls = stats_daily.number_of_crawls + 1,
                requests_retry_count = stats_daily.requests_retry_count + %s,
                requests_scheduler_enqueued_disk =
                    stats_daily.requests_scheduler_enqueued_disk + %s,
                requests_scheduler_enqueued_memory =
                    stats_daily.requests_scheduler_enqueued_memory + %s,
                requests_scheduler_dequeued_disk =
                    stats_daily.requests_scheduler_dequeued_disk + %s,
                requests_scheduler_dequeued_memory =
                    stats_daily.requests_scheduler_dequeued_memory + %s
                ''',
            (spider.name,
                self.namespace,
                today,
                stats.get('retry/count', 0),
                stats.get('scheduler/enqueued/disk', 0),
                stats.get('scheduler/enqueued/memory', 0),
                stats.get('scheduler/dequeued/disk', 0),
                stats.get('scheduler/dequeued/memory', 0),
                stats.get('retry/count', 0),
                stats.get('scheduler/enqueued/disk', 0),
                stats.get('scheduler/enqueued/memory', 0),
                stats.get('scheduler/dequeued/disk', 0),
                stats.get('scheduler/dequeued/memory', 0),
            ))

        self.conn.commit()
