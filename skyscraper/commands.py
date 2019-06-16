import click
import os
import time
import logging

import skyscraper.execution
import skyscraper.git
import skyscraper.mail
import skyscraper.settings


@click.command()
def skyscraper_service():
    """Runs the skyscraper service which determines when spiders have to be
    executed and executes them"""

    proxy = None
    if os.environ.get('SKYSCRAPER_TOR_PROXY'):
        proxy = os.environ.get('SKYSCRAPER_TOR_PROXY')

    repo = skyscraper.git.DeclarativeRepository(
        skyscraper.settings.GIT_REPOSITORY,
        skyscraper.settings.GIT_WORKDIR,
        skyscraper.settings.GIT_SUBFOLDER,
        skyscraper.settings.GIT_BRANCH
    )
    spider_runner = skyscraper.execution.SpiderRunner(proxy)
    runner = skyscraper.execution.SkyscraperRunner(spider_runner)

    try:
        while True:
            repo.update()
            configs = repo.get_all_configs()
            runner.update_spider_config(configs)

            logging.debug('Running due spiders')
            runner.run_due_spiders()

            time.sleep(15)
    except KeyboardInterrupt:
        print('Shutdown requested by user.')


@click.command()
@click.argument('namespace')
@click.argument('spider')
@click.option('--use-tor', is_flag=True, help='Use the TOR network')
def skyscraper_spider(namespace, spider, use_tor):
    """Perform a manual crawl. The user can define the name of the
    namespace and the spider that should be executed.
    """
    proxy = None
    if os.environ.get('SKYSCRAPER_TOR_PROXY'):
        proxy = os.environ.get('SKYSCRAPER_TOR_PROXY')

    click.echo('Executing spider %s/%s.' % (namespace, spider))

    options = {'tor': True} if use_tor else {}
    runner = skyscraper.execution.SpiderRunner(proxy)
    runner.run(namespace, spider, semaphore=None, options=options)
