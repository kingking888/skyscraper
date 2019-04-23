import os
import subprocess


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
            SET blocked_from_running_until = NOW() + INTERVAL '%s minutes'
            -- fail if somebody else blocked it
            WHERE (
                blocked_from_running_until IS NULL
                OR blocked_from_running_until < NOW()
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
            WHERE blocked_from_running_until >= NOW()
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
