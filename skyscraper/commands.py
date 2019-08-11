import click
import os
import time
import logging
import prometheus_client

import skyscraper.archive
import skyscraper.execution
import skyscraper.git
import skyscraper.mail
import skyscraper.settings
import skyscraper.instrumentation


@click.command()
def skyscraper_service():
    """Runs the skyscraper service which determines when spiders have to be
    executed and executes them"""

    prometheus_client.start_http_server(8000)
    prometheus_num_configs = prometheus_client.Gauge(
        'skyscraper_git_spiders',
        'Number of spiders available in the Skyscraper git repository')

    proxy = None
    if os.environ.get('SKYSCRAPER_TOR_PROXY'):
        proxy = os.environ.get('SKYSCRAPER_TOR_PROXY')

    repo = skyscraper.git.DeclarativeRepository(
        skyscraper.settings.GIT_REPOSITORY,
        skyscraper.settings.GIT_WORKDIR,
        skyscraper.settings.GIT_SUBFOLDER,
        skyscraper.settings.GIT_BRANCH
    )
    spider_runners = {
        'scrapy': skyscraper.execution.ScrapySpiderRunner(proxy),
    }
    runner = skyscraper.execution.SkyscraperRunner(spider_runners)

    try:
        while True:
            skyscraper.instrumentation.instrument_num_files()

            repo.update()
            configs = repo.get_all_configs()
            prometheus_num_configs.set(len(configs))
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
    runner = skyscraper.execution.ScrapySpiderRunner(proxy)
    runner.run(namespace, spider, semaphore=None, options=options)


@click.command()
def skyscraper_archive():
    """Archive files from previous months into gzip files."""

    root_folder = skyscraper.settings.SKYSCRAPER_STORAGE_FOLDER_PATH
    for project in os.listdir(root_folder):
        if os.path.isdir(os.path.join(root_folder, project)):
            for spider in os.listdir(os.path.join(root_folder, project)):
                if os.path.isdir(os.path.join(root_folder, project, spider)):
                    click.echo('Archiving old files for {}/{}'.format(
                        project, spider))

                    skyscraper.archive.archive_old_files(
                        os.path.join(root_folder, project, spider))
