import pytest
import moto
import boto3

from skyscraper.spiderloader import S3SpiderLoader


@pytest.fixture
def s3_conn():
    moto.mock_s3().start()

    session = boto3.Session(
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    s3 = session.resource('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='spiders')

    object = s3.Object('spiders', 'namespace/samplespider.py')
    object.put(Body=b'# this would be spider code in real use cases\nimport scrapy\nclass SampleSpider(scrapy.Spider):\n    name = "samplespider"')

    # Yield and then close mock, because we want the mock to exist in the real
    # test functions
    # Do not use mock_* again for the test functions then
    yield s3

    moto.mock_s3().stop()


def test_load_spider_from_s3(s3_conn):
    session = boto3.Session(
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )

    loader = S3SpiderLoader(session, 'spiders', 'namespace',
                            ['skyscraper.spiders'])
    spider = loader.load('samplespider')

    assert spider.name == 'samplespider'
