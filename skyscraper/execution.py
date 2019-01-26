import os
import subprocess


class SpiderRunner():
    def run(self, namespace, spider, options={}):
        if 'tor' in options and options['tor']:
            self._set_proxy_tor()

        # TODO: can we do this directly within Python?
        p = subprocess.Popen([
            "scrapy",
            "crawl",
            spider,
            "-s", "USER_NAMESPACE=%s" % (namespace)
        ])
        p.wait()

    def _set_proxy_tor(self):
        # TODO: What happens if we run multiple instances of Skyscraper
        # on one host? Will all of them have http_proxy set if one of them
        # sets it?
        os.environ['http_proxy'] = 'http://127.0.0.1:8118'
        os.environ['https_proxy'] = 'https://127.0.0.1:8118'
