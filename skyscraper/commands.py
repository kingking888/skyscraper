import click
import os
import time
import logging
import prometheus_client
import asyncio
import pyppeteer

import skyscraper.archive
import skyscraper.execution
import skyscraper.git
import skyscraper.mail
import skyscraper.settings
import skyscraper.spiderloader
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
    spiderloader = skyscraper.spiderloader.GitSpiderLoader(repo)

    browser = pyppeteer.launch()
    spider_runners = {
        'scrapy': skyscraper.execution.ScrapySpiderRunner(proxy),
        'chrome': skyscraper.execution.ChromeSpiderRunner(
            browser, spiderloader),
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
@click.option('--engine', help='Select the engine to use for this spider')
@click.option('--use-tor', is_flag=True, help='Use the TOR network')
def skyscraper_spider(namespace, spider, engine, use_tor):
    """Perform a manual crawl. The user can define the name of the
    namespace and the spider that should be executed.
    """
    proxy = None
    if os.environ.get('SKYSCRAPER_TOR_PROXY'):
        proxy = os.environ.get('SKYSCRAPER_TOR_PROXY')

    click.echo('Executing spider %s/%s.' % (namespace, spider))

    repo = skyscraper.git.DeclarativeRepository(
        skyscraper.settings.GIT_REPOSITORY,
        skyscraper.settings.GIT_WORKDIR,
        skyscraper.settings.GIT_SUBFOLDER,
        skyscraper.settings.GIT_BRANCH
    )
    spiderloader = skyscraper.spiderloader.GitSpiderLoader(repo)

    options = {'tor': True} if use_tor else {}
    if engine == 'chrome':
        async def run_chrome():
            browser = pyppeteer.launch()
            runner = skyscraper.execution.ChromeSpiderRunner(
                browser, spiderloader)
            await runner.run(namespace, spider)
            await runner.close()

        asyncio.get_event_loop().run_until_complete(run_chrome())
    else:
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
