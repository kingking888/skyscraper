import collections

from skyscraper.config import Configuration
from skyscraper.execution import SkyscraperRunner


class MockSpiderRunner(object):
    def __init__(self):
        self.spiders_run = collections.defaultdict(dict)

    def run_standalone(self, project, spider):
        self.spiders_run[project][spider] = True


def test_skyscraper_runner_runs_due_spiders():
    spider_runner = MockSpiderRunner()

    skyscraper_runner = SkyscraperRunner(spider_runner)

    c = Configuration('my-project', 'my-spider')
    c.recurrence_minutes = 120
    c.enabled = True

    skyscraper_runner.update_spider_config([c])

    skyscraper_runner.run_due_spiders()

    assert spider_runner.spiders_run['my-project']['my-spider'] is True
