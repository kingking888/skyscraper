import os
import subprocess


class SpiderRunner():
    def __init__(self, http_proxy):
        self.http_proxy = http_proxy

    def run(self, namespace, spider, options={}):
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

    def _set_proxy_tor(self):
        if not self.http_proxy:
            raise ValueError('No http proxy was configured, but this is '
                             'required if TOR is enabled for a spider')

        # TODO: What happens if we run multiple instances of Skyscraper
        # on one host? Will all of them have http_proxy set if one of them
        # sets it?
        os.environ['http_proxy'] = 'http://{}'.format(self.http_proxy)
        os.environ['https_proxy'] = 'https://{}'.format(self.http_proxy)
