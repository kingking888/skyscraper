import pytest

from skyscraper.spiderloader import PostgresSpiderLoader


@pytest.fixture
def postgresdb(conn):
    code = '''import scrapy
class MySpider(scrapy.Spider):
    name = 'samplespider'
    '''

    c = conn.cursor()
    c.execute("INSERT INTO projects (name) VALUES ('unit-tests')")
    c.execute(
        """INSERT INTO skyscraper_spiders
        (name, project_id, code, recurrency_minutes)
        VALUES (
            'samplespider',
            (SELECT project_id FROM projects WHERE name = 'unit-tests'),
            %s,
            60)""",
        (code,))
    conn.commit()

    yield conn

    c.execute(
        '''DELETE FROM skyscraper_spiders
        WHERE project_id = (
            SELECT project_id FROM projects
            WHERE name = 'unit-tests'
        )''')
    c.execute("""DELETE FROM projects
        WHERE name = 'unit-tests'""")
    conn.commit()


def test_load_spider_from_postgres(postgresdb):
    loader = PostgresSpiderLoader(
            postgresdb,
            'unit-tests',
            ['skyscraper.spiders'])
    spider = loader.load('samplespider')

    assert spider.name == 'samplespider'
