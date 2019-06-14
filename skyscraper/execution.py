import os
import subprocess
import datetime
import heapq
import collections
import logging


class SkyscraperRunner(object):
    def __init__(self, spider_runner):
        self.next_scheduled_runtimes = []
        self.spider_config = collections.defaultdict(dict)

        self.spider_runner = spider_runner

    def update_spider_config(self, configs):
        for config in configs:
            self.spider_config[config.project][config.spider] = config

            if not self._spider_already_scheduled(
                    config.project, config.spider):
                heapq.heappush(self.next_scheduled_runtimes,
                    (datetime.datetime.utcnow(),
                    (config.project, config.spider)))

    def run_due_spiders(self):
        # heaps are sorted in python
        # https://docs.python.org/3.1/library/heapq.html
        while datetime.datetime.utcnow() > self.next_scheduled_runtimes[0][0]:
            item = heapq.heappop(self.next_scheduled_runtimes)
            project, spider = item[1]

            self.spider_runner.run(project, spider)

            self._reschedule_spider(project, spider)

    def _spider_already_scheduled(self, project, spider):
        for _, (p, s) in self.next_scheduled_runtimes:
            if p == project and s == spider:
                return True

        return False

    def _reschedule_spider(self, project, spider):
        try:
            config = self.spider_config[project][spider]

            # if there is a recurrency defined, schedule it again
            if config.recurrency_minutes:
                logging.debug('Rescheduling spider {}/{} in {} min.'.format(
                    project, spider, config.recurrency_minutes))

                next_runtime = datetime.datetime.utcnow() \
                    + datetime.timedelta(minutes=config.recurrency_minutes)
                heapq.heappush(
                    self.next_scheduled_runtimes,
                    (next_runtime, (project, spider)))
        except KeyError:
            # spider was removed, do not schedule again
            pass


class SpiderRunner(object):
    """This class is a runner to help with the execution of spiders with
    a given configuration. It sets up the environment and configurations
    and then executes the spider.
    """
    def __init__(self, http_proxy):
        self.http_proxy = http_proxy

    def run(self, namespace, spider, semaphore=None, options={}):
        """Run the given spider with the defined options. Will block
        until the spider has finished.
        """
        if not self._acquire_run_lock(semaphore):
            return

        if 'tor' in options and options['tor']:
            self._set_proxy_tor()

        # TODO: can we do this directly within Python?
        command = [
            "scrapy",
            "crawl",
            spider,
            "-s", "USER_NAMESPACE=%s" % (namespace),
        ]

        # set start_urls empty, so that scrapy does not start
        # with the start_url again and instead do the backlog
        if 'backlog' in options and options['backlog']:
            command.append('-a')
            command.append('start_urls=')

        p = subprocess.Popen(command)
        p.wait()

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
