import os
import psycopg2
import pytest


def pytest_configure(config):
    # TODO: make the path flexible if possible, currently this forces us
    # to run the tests from the root folder always
    path = 'tests'
    os.environ['currpath'] = path
    return path


@pytest.mark.usefixtures('currpath')
def execute_sql_file(conn, sql_file):
    currpath = os.environ['currpath']
    sql_file_path = os.path.join(currpath, sql_file)
    cursor = conn.cursor()
    with open(sql_file_path, 'r') as f:
        cursor.execute(f.read())
    conn.commit()


def pytest_runtest_setup(item):
    connstring = os.environ['SKYSCRAPER_UNITTEST_CONNSTRING']

    # Prepare the database, set to an initial state
    conn = psycopg2.connect(connstring)
    execute_sql_file(conn, 'clear-database.sql')
    execute_sql_file(conn, 'fill-database.sql')


def pytest_runtest_teardown(item, nextitem):
    connstring = os.environ['SKYSCRAPER_UNITTEST_CONNSTRING']

    conn = psycopg2.connect(connstring)
    execute_sql_file(conn, 'clear-database.sql')


@pytest.fixture
def conn():
    connstring = os.environ['SKYSCRAPER_UNITTEST_CONNSTRING']
    return psycopg2.connect(connstring)
