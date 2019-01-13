import pytest
import unittest.mock
import moto
import boto3
from boto3.dynamodb.conditions import Key
import json
import datetime

from scrapy.spiders import Spider
import scrapy.exceptions

from skyscraper.pipelines.mqtt import MqttOutputPipeline
from skyscraper.pipelines.aws import SaveDataToS3Pipeline
from skyscraper.pipelines.aws import DoNotStoreDuplicatesPipeline
from skyscraper.pipelines.aws import StoreItemToDuplicateFilterPipeline
from skyscraper.items import BasicItem


@pytest.fixture
def s3_conn():
    moto.mock_s3().start()

    session = boto3.Session(
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    s3 = session.resource('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='skyscraper-data')

    # Yield and then close mock, because we want the mock to exist in the real
    # test functions
    # Do not use mock_* again for the test functions then
    yield s3

    moto.mock_s3().stop()


@pytest.fixture
def dynamodb_table():
    moto.mock_dynamodb2().start()

    session = boto3.Session(
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    dynamodb = session.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='CrawlingLog',
        KeySchema=[{
            'AttributeName': 'Namespace',
            'KeyType': 'HASH'
        }, {
            'AttributeName': 'Id',
            'KeyType': 'RANGE',
        }],
        AttributeDefinitions=[{
            'AttributeName': 'Namespace',
            'AttributeType': 'S'
        }, {
            'AttributeName': 'Id',
            'AttributeType': 'S'
        }],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
        }
    )

    yield table

    moto.mock_dynamodb2().stop()


@pytest.fixture
def mqtt_client():
    client = unittest.mock.Mock()

    return client


def test_save_data_pipeline_to_s3_does_store(s3_conn):
    pipeline = SaveDataToS3Pipeline(
        s3_conn.Bucket('skyscraper-data'),
        'namespace')

    spider = Spider(name='spider')
    item = BasicItem()
    item['id'] = 'my-unique-id'
    item['url'] = 'http://example.com/'
    item['source'] = 'dummy source'
    pipeline.process_item(item, spider)
    pipeline.close_spider(spider)

    objs = [obj for obj in s3_conn.Bucket('skyscraper-data').objects.all()]
    assert len(objs) == 1


def test_save_store_dup_pipeline_does_keep_duplicates_log(dynamodb_table):
    pipeline = StoreItemToDuplicateFilterPipeline(
        dynamodb_table,
        'namespace')

    spider = Spider(name='spider')
    item = BasicItem()
    item['id'] = 'my-unique-id'
    item['url'] = 'http://example.com/'
    item['source'] = 'dummy source'
    item['crawl_time'] = \
        datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    pipeline.process_item(item, spider)
    pipeline.close_spider(spider)

    response = dynamodb_table.query(
        KeyConditionExpression=Key('Namespace').eq('namespace')
        & Key('Id').eq(item['id']))

    assert response['Count'] == 1


def test_duplicate_detection_pipeline(dynamodb_table):
    spider = Spider(name='spider')

    item = {
        'id': 'myspider-myuniqueid',
        'url': 'https://localhost/',
        'crawl_time': '2018-01-01T20:00:00',
    }
    dynamodb_table.put_item(Item={
        'Namespace': 'my-namespace',
        'Id': item['id'],
        'CrawlTime': item['crawl_time'],
        'Url': item['url'],
        'Spider': spider.name
    })

    pipeline = DoNotStoreDuplicatesPipeline(dynamodb_table, 'my-namespace')
    with pytest.raises(scrapy.exceptions.DropItem):
        pipeline.process_item(item, spider)

    new_item = {
        'id': 'myspider-myotherid',
        'url': 'https://localhost/resource',
        'crawl_time': '2018-01-01T20:00:05',
    }

    pipeline.process_item(new_item, spider)


def test_mqtt_pipeline_does_send_item(mqtt_client):
    spider = Spider(name='spider')
    pipeline = MqttOutputPipeline(mqtt_client, 'dummy-namespace')

    item = BasicItem()
    item['url'] = 'http://example.com/'
    item['source'] = 'dummy source'

    pipeline.process_item(item, spider)

    args = mqtt_client.publish.call_args
    topic = args[0][0]
    payload = json.loads(args[0][1])

    assert topic == 'skyscraper/items/dummy-namespace/spider'
    assert payload['url'] == 'http://example.com/'
    assert payload['source'] == 'dummy source'
    assert payload['namespace'] == 'dummy-namespace'


def test_mqtt_pipeline_does_return_item_after_process(mqtt_client):
    spider = Spider(name='spider')
    pipeline = MqttOutputPipeline(mqtt_client, 'dummy-namespace')

    item = BasicItem()
    item['url'] = 'http://example.com/'
    item['source'] = 'dummy source'

    ret = pipeline.process_item(item, spider)

    assert ret is not None
