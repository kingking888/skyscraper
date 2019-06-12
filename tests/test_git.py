import pytest
import tempfile
import subprocess
import os
import shutil

from skyscraper.git import DeclarativeRepository


@pytest.fixture
def gitfolder():
    path = tempfile.mkdtemp()

    subprocess.call(['git', 'init', path])

    subprocess.call(
        ['git', 'config', 'user.email', 'unittest@example.com'],
        cwd=path)
    subprocess.call(['git', 'config', 'user.name', 'Unit Test'], cwd=path)

    # Must create a single file to be able to commit master branch
    with open(os.path.join(path, 'README.md'), 'w') as f:
        f.write('Unit test\n')
    subprocess.call(['git', 'add', '.'], cwd=path)
    subprocess.call(['git', 'commit', '-m', 'add readme'], cwd=path)

    # Switch branch and create the spider
    # (normally your master would be ahead of production, but for testing
    # whether the git loader can find the spider it is better to have the
    # spider only on production)
    subprocess.call(['git', 'checkout', '-b', 'production'], cwd=path)

    os.mkdir(os.path.join(path, 'myproject'))

    spiderfile = os.path.join(path, 'myproject', 'myspider.py')
    with open(spiderfile, 'w') as f:
        f.write('import scrapy\n')
        f.write('class MySpider(scrapy.Spider):\n')
        f.write('    name = "myspider"\n')

    subprocess.call(['git', 'add', '.'], cwd=path)
    subprocess.call(['git', 'commit', '-m', 'add sample spider'], cwd=path)

    # Switch back to master branch, so that the spider is not visible at first
    subprocess.call(['git', 'checkout', 'master'], cwd=path)

    yield path

    shutil.rmtree(path)


def test_load_spider_from_repo(gitfolder):
    workdir = tempfile.mkdtemp()
    repo = DeclarativeRepository(gitfolder, workdir, branch='production')
    spider = repo.load_spider('myproject', 'myspider')

    assert spider.name == 'myspider'

    shutil.rmtree(workdir)


def test_list_spiders(gitfolder):
    workdir = tempfile.mkdtemp()
    repo = DeclarativeRepository(gitfolder, workdir, branch='production')
    spiders = list(repo.iterate_spiders())

    assert spiders == [('myproject', 'myspider')]

    shutil.rmtree(workdir)
