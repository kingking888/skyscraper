import click
import subprocess
import datetime

import skyscraper.db
import skyscraper.mail


@click.group()
@click.pass_context
def skyscrapercli(ctx):
    ctx.obj = {}
    ctx.obj['conn'] = skyscraper.db.get_postgres_conn()


@click.command(name='crawl-next-scheduled')
@click.pass_context
def crawl_next_scheduled(ctx):
    conn = ctx.obj['conn']
    namespace, spider = skyscraper.db.next_scheduled_spider(conn)

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
        # TODO: can we do this directly within Python?
        p = subprocess.Popen([
            "scrapy",
            "crawl",
            spider,
            "-s", "USER_NAMESPACE=%s" % (namespace)
        ])
        p.wait()


@click.command(name='show-next-scheduled')
@click.pass_context
def show_next_scheduled(ctx):
    conn = ctx.obj['conn']
    namespace, spider = skyscraper.db.next_scheduled_spider(conn)

    if namespace is None or spider is None:
        click.echo('No spider is scheduled for execution.')
    else:
        click.echo('Next spider is %s/%s.' % (namespace, spider))


@click.command(name='crawl-manual')
@click.argument('namespace')
@click.argument('spider')
def crawl_manual(namespace, spider):
    click.echo('Executing spider %s/%s.' % (namespace, spider))

    # TODO: can we do this directly within Python?
    p = subprocess.Popen([
        "scrapy",
        "crawl",
        spider,
        "-s", "USER_NAMESPACE=%s" % (namespace)
    ])
    p.wait()


@click.command(name='check-item-count')
@click.option('--send-mail', is_flag=True, default=False)
@click.pass_context
def check_item_count(ctx, send_mail):
    conn = ctx.obj['conn']

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


skyscrapercli.add_command(crawl_next_scheduled)
skyscrapercli.add_command(show_next_scheduled)
skyscrapercli.add_command(crawl_manual)
skyscrapercli.add_command(check_item_count)
