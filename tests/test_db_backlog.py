import pytest

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
            next_scheduled_runtime, use_tor)
        VALUES (
            'samplespider',
            (SELECT project_id FROM projects WHERE name = 'unit-tests'),
            '',
            60,
            NOW() - INTERVAL '1 hour',
            true)""")
    c.execute(
        """INSERT INTO skyscraper_spiders
        (name, project_id, code, recurrency_minutes,
            next_scheduled_runtime, use_tor)
        VALUES (
            'older-spider',
            (SELECT project_id FROM projects WHERE name = 'unit-tests'),
            '',
            60,
            NOW() - INTERVAL '12 hour',
            true)""")
    c.execute(
        """INSERT INTO skyscraper_requests
        (request_id, spider_id, priority, url, method, create_date)
        VALUES (
            'a9225ec5-e593-4132-b428-26d8aa8ca89d',
            (SELECT spider_id FROM skyscraper_spiders
                WHERE name = 'samplespider'),
            0,
            'http://example.com/',
            'GET',
            NOW())""")

    conn.commit()

    yield conn


def test_next_backlog_spider_has_biggest_backlog(postgresdb):
    namespace, spider, _ = \
        skyscraper.db.spider_with_biggest_backlog(postgresdb)

    assert namespace == 'unit-tests'
    assert spider == 'samplespider'


def test_next_backlog_spider_returns_tor_option(postgresdb):
    namespace, spider, option = \
        skyscraper.db.spider_with_biggest_backlog(postgresdb)

    assert namespace == 'unit-tests'
    assert spider == 'samplespider'
    assert option['tor']
