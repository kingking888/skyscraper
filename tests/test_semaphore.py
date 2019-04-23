import pytest

from skyscraper.execution import Semaphore


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
    conn.commit()

    yield conn


def test_semaphore_test_acquiring(postgresdb):
    s = Semaphore(postgresdb, 'unit-tests', 'samplespider')
    s.acquire()
    assert s.locked()

    with pytest.raises(Exception):
        s.acquire()

    s.release()
    s.acquire()

    assert s.locked()
