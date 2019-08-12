import os
import subprocess
import datetime
import heapq
import collections
import logging
import prometheus_client
import asyncio

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


SPIDERS_EXECUTED_COUNT = prometheus_client.Counter(
    'skyscraper_executed_spiders',
    'Counter for the number of executed spiders')


class SkyscraperRunner(object):
    def __init__(self, spider_runners):
        self.next_scheduled_runtimes = []
        self.spider_config = collections.defaultdict(dict)

        self.spider_runners = spider_runners

    def update_spider_config(self, configs):
        for config in configs:
            if not config.enabled:
                continue

            if self._has_new_config(config.project, config.spider, config):
                self.spider_config[config.project][config.spider] = config

                # TODO: When pushing a spider due to new configuration
                # all previous schedules of the same spider have to be removed
                # from the schedule (otherwise they will trigger reschedules
                # over and over)
                heapq.heappush(self.next_scheduled_runtimes,
                    (datetime.datetime.utcnow(),
                    (config.engine, config.project, config.spider)))

    def run_due_spiders(self):
        # heaps are sorted in python
        # https://docs.python.org/3.1/library/heapq.html
        while len(self.next_scheduled_runtimes) > 0 \
                and datetime.datetime.utcnow() > self.next_scheduled_runtimes[0][0]:

            item = heapq.heappop(self.next_scheduled_runtimes)
            engine, project, spider = item[1]

            SPIDERS_EXECUTED_COUNT.inc()
            runner = self.spider_runners.get(engine, None)
            if not runner:
                raise ValueError('Unknown scraping engine "{}"'.format(engine))

            # TODO: This method should be called run(), but this will require
            # some refactoring on the ScrapySpiderRunner
            runner.run_standalone(project, spider)

            self._reschedule_spider(engine, project, spider)

    def _has_new_config(self, project, spider, config):
        try:
            old_conf = self.spider_config[project][spider]
            return hash(config) != hash(old_conf)
        except KeyError:
            # does not exist yet = is new config
            return True

    def _reschedule_spider(self, engine, project, spider):
        try:
            config = self.spider_config[project][spider]

            # if there is a recurrence defined, schedule it again
            if config.recurrence_minutes:
                logging.debug('Rescheduling spider {}/{} in {} min.'.format(
                    project, spider, config.recurrence_minutes))

                next_runtime = datetime.datetime.utcnow() \
                    + datetime.timedelta(minutes=config.recurrence_minutes)
                heapq.heappush(
                    self.next_scheduled_runtimes,
                    (next_runtime, (engine, project, spider)))
        except KeyError:
            # spider was removed, do not schedule again
            pass


class ScrapySpiderRunner(object):
    """This class is a runner to help with the execution of spiders with
    a given configuration. It sets up the environment and configurations
    and then executes the spider.
    """
    def __init__(self, http_proxy):
        self.http_proxy = http_proxy

    def run_standalone(self, namespace, spider, options={}):
        command = [
            'skyscraper-spider',
            namespace,
            spider,
        ]

        if 'tor' in options and options['tor']:
            command.append('--use-tor')

        subprocess.call(command)

    def run(self, namespace, spider, semaphore=None, options={}):
        """Run the given spider with the defined options. Will block
        until the spider has finished.
        """
        if not self._acquire_run_lock(semaphore):
            return

        if 'tor' in options and options['tor']:
            self._set_proxy_tor()

        # Start the spider in this process
        settings = get_project_settings()
        settings['USER_NAMESPACE'] = namespace
        process = CrawlerProcess(settings)
        process.crawl(spider)
        process.start()

        self._release_run_lock(semaphore)

    def _set_proxy_tor(self):
        if not self.http_proxy:
            raise ValueError('No http proxy was configured, but this is '
                             'required if TOR is enabled for a spider')

        # TODO: What happens if we run multiple instances of Skyscraper
        # on one host? Will all of them have http_proxy set if one of them
        # sets it?
        os.environ['http_proxy'] = 'http://{}'.format(self.http_proxy)
        os.environ['https_proxy'] = 'https://{}'.format(self.http_proxy)

    def _acquire_run_lock(self, semaphore):
        if not semaphore:
            return True
        else:
            try:
                semaphore.acquire()
                return True
            except Exception:
                return False

    def _release_run_lock(self, semaphore):
        if semaphore:
            semaphore.release()


class ChromeSpiderRunner(object):
    def __init__(self, browser_future, spider_loader):
        # TODO: Improve the async stuff, we actually only need sync
        # execution
        self.browser_future = browser_future
        self.browser = None
        self.spider_loader = spider_loader

    def run_standalone(self, project, spider):
        asyncio.get_event_loop().run_until_complete(self.run(project, spider))

    async def run(self, project, spider):
        # TODO:
        # 1. load spider with spiderloader here
        # 2. read the start urls
        # 3. iterate start urls and emitted requests and run all emitted
        #    BasicItems through the pipeline steps
        if not self.browser:
            self.browser = await self.browser_future
        spider_class = self.spider_loader.load(spider, namespace=project)
        spider = spider_class()
        frontier = spider.start_urls

        for url in frontier:
            page = await self.browser.newPage()
            response = await page.goto(url)

            res = await spider.parse(page, response)
            print(res)

    async def close(self):
        await self.browser.close()


class Semaphore(object):
    def __init__(self, conn, namespace, spider):
        self.conn = conn
        self.namespace = namespace
        self.spider = spider
        self.timeout_minutes = 60

    def acquire(self):
        c = self.conn.cursor()
        c.execute('''UPDATE skyscraper_spiders
            SET blocked_from_running_until = NOW() at time zone 'utc'
                + INTERVAL '%s minutes'
            -- fail if somebody else blocked it
            WHERE (
                blocked_from_running_until IS NULL
                OR blocked_from_running_until < NOW() at time zone 'utc'
            )
            AND name = %s
            AND project_id IN (
                SELECT project_id FROM projects WHERE name = %s
            )''',
            (self.timeout_minutes, self.spider, self.namespace))
        self.conn.commit()

        if c.rowcount == 0:
            raise Exception('Could not acquire lock')

    def locked(self):
        c = self.conn.cursor()
        c.execute('''SELECT COUNT(*) FROM skyscraper_spiders s
            JOIN projects p ON s.project_id = p.project_id
            WHERE blocked_from_running_until >= NOW() at time zone 'utc'
            AND s.name = %s
            AND p.name = %s''', (self.spider, self.namespace))
        row = c.fetchone()
        return row is not None

    def release(self):
        c = self.conn.cursor()
        c.execute('''UPDATE skyscraper_spiders
            SET blocked_from_running_until = NULL
            WHERE name = %s
            AND project_id IN (
                SELECT project_id FROM projects WHERE name = %s
            )''', (self.spider, self.namespace))
        self.conn.commit()
