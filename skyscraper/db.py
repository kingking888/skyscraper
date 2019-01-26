import psycopg2

from scrapy.utils.project import get_project_settings


def get_postgres_conn():
    settings = get_project_settings()
    connstring = settings.get('POSTGRES_CONNSTRING')

    return psycopg2.connect(connstring)


def next_scheduled_spider(conn):
    c = conn.cursor()

    c.execute('''SELECT p.name, s.name, s.use_tor
        FROM skyscraper_spiders s
        JOIN projects p ON p.project_id = s.project_id
        WHERE s.next_scheduled_runtime <= NOW() at time zone 'utc'
            OR s.next_scheduled_runtime IS NULL
        ORDER BY s.next_scheduled_runtime ASC NULLS FIRST''')
    row = c.fetchone()

    if row is None:
        return None, None, {}
    else:
        options = {'tor': True} if row[2] else {}
        return row[0], row[1], options


def update_schedule(conn, project, spider):
    c = conn.cursor()

    c.execute('''UPDATE skyscraper_spiders
        SET next_scheduled_runtime =
            NOW() at time zone 'utc' + interval '1 minute' * recurrency_minutes
        WHERE project_id = (SELECT project_id FROM projects WHERE name = %s)
        AND name = %s''', (project, spider))
    conn.commit()


def spider_with_biggest_backlog(conn):
    c = conn.cursor()

    c.execute('''SELECT p.name, s.name, s.use_tor
        FROM skyscraper_requests r
        JOIN skyscraper_spiders s ON r.spider_id = s.spider_id
        JOIN projects p ON p.project_id = s.project_id
        GROUP BY r.spider_id, p.name, s.name, s.use_tor
        ORDER BY COUNT(r.*)
        LIMIT 1''')
    row = c.fetchone()

    if row is None:
        return None, None, {}
    else:
        options = {'tor': True} if row[2] else {}
        return row[0], row[1], options


def get_spiders_below_item_count_threshold(conn, date):
    c = conn.cursor()

    c.execute('''SELECT p.name, s.name,
        COALESCE(sd.items_scraped_count, 0) AS items_scraped_count,
        s.items_scraped_daily_threshold,
        u.email
        FROM skyscraper_spiders s
        JOIN projects p
            ON p.project_id = s.project_id
        JOIN users_projects up
            ON p.project_id = up.project_id
        JOIN users u
            ON u.user_id = up.user_id
        -- use a left outer join with the date in the join condition
        -- to ensure that spiders that have no entries in stats table, yet,
        -- get associated with 0 scraped items
        -- otherwise we would not find these as spiders with too few items
        LEFT OUTER JOIN skyscraper_spiders_stats_daily sd
            ON s.spider_id = sd.spider_id
            AND sd.stats_date = %s
        -- if the threshold is set to 0 a scrape count of NULL (i.e. not
        -- in DB yet for this day) is OK, because NULL also means 0 items
        WHERE (sd.items_scraped_count IS NULL
            AND s.items_scraped_daily_threshold > 0)
            OR sd.items_scraped_count < s.items_scraped_daily_threshold
        ORDER BY p.name, s.name''', (date,))
    return c.fetchall()
