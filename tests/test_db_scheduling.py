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
    conn.commit()

    yield conn


def test_next_scheduled_spider_has_lowest_runtime(postgresdb):
    namespace, spider, _ = skyscraper.db.next_scheduled_spider(postgresdb)

    assert namespace == 'unit-tests'
    assert spider == 'older-spider'


def test_updated_spider_has_refreshed_date(postgresdb):
    namespace1, spider1, _ = skyscraper.db.next_scheduled_spider(postgresdb)
    skyscraper.db.update_schedule(postgresdb, namespace1, spider1)

    namespace2, spider2, _ = skyscraper.db.next_scheduled_spider(postgresdb)

    assert spider1 != spider2
    assert namespace2 == 'unit-tests'
    assert spider2 == 'samplespider'


def test_next_scheduled_spider_does_include_tor_option(postgresdb):
    namespace, spider, option = skyscraper.db.next_scheduled_spider(postgresdb)

    assert namespace == 'unit-tests'
    assert spider == 'older-spider'
    assert option['tor']
