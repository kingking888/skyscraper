import pytest
import datetime

import skyscraper.db


@pytest.fixture
def postgresdb(conn):
    c = conn.cursor()
    c.execute("INSERT INTO projects (name) VALUES ('unit-tests')")
    c.execute("""INSERT INTO users_projects (user_id, project_id)
        VALUES
        (
            (SELECT user_id FROM users WHERE username = 'test-user'),
            (SELECT project_id FROM projects WHERE name = 'unit-tests')
        )""")
    c.execute(
        """INSERT INTO skyscraper_spiders
        (name, project_id, code, recurrency_minutes,
            items_scraped_daily_threshold)
        VALUES (
            'samplespider',
            (SELECT project_id FROM projects WHERE name = 'unit-tests'),
            '',
            60,
            10)""")
    conn.commit()

    yield conn


def test_can_find_spiders_with_too_few_items(postgresdb):
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    info = skyscraper.db.get_spiders_below_item_count_threshold(
        postgresdb, today)

    assert len(info) == 1
    assert info[0][1] == 'samplespider'
    assert info[0][2] == 0
    assert info[0][3] == 10


def test_does_not_find_spiders_with_enough_items(postgresdb):
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')

    c = postgresdb.cursor()
    c.execute('''INSERT INTO skyscraper_spiders_stats_daily
        (spider_id, stats_date, items_scraped_count)
        VALUES
        (
            (SELECT spider_id FROM skyscraper_spiders
                WHERE name = 'samplespider'),
            %s,
            20
        )''', (today,))
    postgresdb.commit()

    info = skyscraper.db.get_spiders_below_item_count_threshold(
        postgresdb, today)

    assert len(info) == 0
