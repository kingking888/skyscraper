import click
import datetime
import os

import skyscraper.db
import skyscraper.mail
import skyscraper.execution


@click.group()
@click.pass_context
def skyscrapercli(ctx):
    proxy = None
    if os.environ.get('SKYSCRAPER_TOR_PROXY'):
        proxy = os.environ.get('SKYSCRAPER_TOR_PROXY')

    ctx.obj = {
        'proxy': proxy
    }


@click.command(name='crawl-scheduled-or-backlog')
@click.pass_context
def crawl_scheduled_or_backlog(ctx):
    """Either perform a scheduled crawl for the next scheduled spider
    or if no scheduled spider is due perform a backlog crawl. If no backlog
    requests are available either, do nothing
    """
    conn = skyscraper.db.get_postgres_conn()
    namespace, spider, options = skyscraper.db.next_scheduled_spider(conn)

    if namespace is not None and spider is not None:
        click.echo(
            'Increasing next runtime of spider %s/%s'
            % (namespace, spider))
        skyscraper.db.update_schedule(conn, namespace, spider)

        click.echo('Executing spider %s/%s.' % (namespace, spider))

        runner = skyscraper.execution.SpiderRunner(ctx.obj['proxy'])
        runner.run(namespace, spider, options)
    else:
        namespace, spider, options = \
            skyscraper.db.spider_with_biggest_backlog(conn)
        # TODO: Or find the one with the most points, but currently
        # we don't count points per project/spider

        if namespace is None or spider is None:
            click.echo('No spider scheduled and no spider has backlog.')
        else:
            click.echo('Crawling backlog for spider %s/%s.'
                       % (namespace, spider))

            options['backlog'] = True
            runner = skyscraper.execution.SpiderRunner(ctx.obj['proxy'])
            runner.run(namespace, spider, options)


@click.command(name='crawl-next-scheduled')
@click.pass_context
def crawl_next_scheduled(ctx):
    """Perform a scheduled crawl for the spider that has the lowest
    next scheduled runtime. The scheduled runtime must be smaller than the
    current time or otherwise this method will do nothing.
    """
    conn = skyscraper.db.get_postgres_conn()
    namespace, spider, options = skyscraper.db.next_scheduled_spider(conn)

    if namespace is None or spider is None:
        click.echo('No spider is scheduled for execution.')
    else:
        # immediately update the next runtime (before actually
        # running the spider) to avoid that other invocations of
        # skyscraper will read the same scheduled spider
        click.echo(
            'Increasing next runtime of spider %s/%s'
            % (namespace, spider))
        skyscraper.db.update_schedule(conn, namespace, spider)

        click.echo('Executing spider %s/%s.' % (namespace, spider))

        runner = skyscraper.execution.SpiderRunner(ctx.obj['proxy'])
        runner.run(namespace, spider, options)


@click.command(name='show-next-scheduled')
@click.pass_context
def show_next_scheduled(ctx):
    """Show the next scheduled spider that has the lowest
    next scheduled runtime, but do not perform an actual crawl.
    """
    conn = skyscraper.db.get_postgres_conn()
    namespace, spider, _ = skyscraper.db.next_scheduled_spider(conn)

    if namespace is None or spider is None:
        click.echo('No spider is scheduled for execution.')
    else:
        click.echo('Next spider is %s/%s.' % (namespace, spider))


@click.command(name='crawl-manual')
@click.argument('namespace')
@click.argument('spider')
@click.option('--use-tor', is_flag=True, help='Use the TOR network')
@click.pass_context
def crawl_manual(ctx, namespace, spider, use_tor):
    """Perform a manual crawl. The user can define the name of the
    namespace and the spider that should be executed.
    """
    click.echo('Executing spider %s/%s.' % (namespace, spider))

    options = {'tor': True} if use_tor else {}
    runner = skyscraper.execution.SpiderRunner(ctx.obj['proxy'])
    runner.run(namespace, spider, options)


@click.command(name='crawl-backlog')
@click.pass_context
def crawl_backlog(ctx):
    """Perform a backlog crawl. This will search for requests in the
    persistent storage and execute them.
    """
    conn = skyscraper.db.get_postgres_conn()
    namespace, spider, options = \
        skyscraper.db.spider_with_biggest_backlog(conn)
    # TODO: Or find the one with the most points, but currently
    # we don't count points per project/spider

    if namespace is None or spider is None:
        click.echo('No spider has backlog.')
    else:
        click.echo('Crawling backlog for spider %s/%s.' % (namespace, spider))

        options['backlog'] = True
        runner = skyscraper.execution.SpiderRunner(ctx.obj['proxy'])
        runner.run(namespace, spider, options)


@click.command(name='check-item-count')
@click.option('--send-mail', is_flag=True, default=False)
@click.pass_context
def check_item_count(ctx, send_mail):
    """Run a plausibility check on the number of crawled items. Each spider
    has a number of minimum items it should crawl per day. This function
    will search for spiders that have crawled less items than required and
    send a notification for them.
    """
    conn = skyscraper.db.get_postgres_conn()

    yesterday_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    yesterday = yesterday_date.strftime('%Y-%m-%d')

    click.echo(
        'Executing item count check for all spiders for %s.' % yesterday)
    info = skyscraper.db.get_spiders_below_item_count_threshold(
        conn, yesterday)

    if len(info):
        for project, spider, count, threshold, mail_owner in info:
            click.echo(
                '- %s/%s (%d < %d)' % (project, spider, count, threshold))

            if send_mail:
                skyscraper.mail.send_treshold_warning_mail(
                    mail_owner, project, spider, count, threshold,
                    'item count')
    else:
        click.echo('No spiders are below threshold.')


skyscrapercli.add_command(crawl_scheduled_or_backlog)
skyscrapercli.add_command(crawl_next_scheduled)
skyscrapercli.add_command(show_next_scheduled)
skyscrapercli.add_command(crawl_manual)
skyscrapercli.add_command(crawl_backlog)
skyscrapercli.add_command(check_item_count)
