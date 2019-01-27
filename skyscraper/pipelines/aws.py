# -*- coding: utf-8 -*-

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json
import datetime
import collections

from scrapy.exporters import PythonItemExporter
from scrapy.exceptions import DropItem


class DoNotStoreDuplicatesPipeline(object):
    """This is a pipeline step that checks whether an item has already been
    scraped before. It is used in combination with
    StoreItemToDuplicateFilterPipeline, which is responsible to store the
    IDs of scraped items.

    If an item has already been scraped before it will be dropped and not
    passed further to other pipeline steps.
    """
    def __init__(self, dynamodb_index, namespace):
        self.namespace = namespace
        self.article_index = dynamodb_index

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        session = boto3.Session(
            aws_access_key_id=settings.get('AWS_ACCESS_KEY'),
            aws_secret_access_key=settings.get('AWS_SECRET_ACCESS_KEY'),
            region_name='us-east-1'
        )
        dynamodb = session.resource('dynamodb')
        dynamodb_index = dynamodb.Table(settings.get('DYNAMODB_CRAWLING_INDEX'))

        namespace = settings.get('USER_NAMESPACE')

        return cls(dynamodb_index, namespace)

    def process_item(self, item, spider):
        response = self.article_index.query(
                KeyConditionExpression=Key('Namespace').eq(self.namespace) \
                        & Key('Id').eq(item['id']))

        if response['Count'] > 0:
            raise DropItem("URL '%s' with item ID '%s' has already been crawled" % (item['url'], item['id']))
        else:
            return item


class StoreItemToDuplicateFilterPipeline(object):
    """This pipeline stores the IDs of scraped items to a persistent
    duplicate filter. It is used in combination with
    DoNotStoreDuplicatesPipeline, which later checks if a spider tries to
    emit an item that has been scraped before.
    """
    def __init__(self, dynamodb_index, namespace):
        self.namespace = namespace

        self.article_index = dynamodb_index

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        session = boto3.Session(
            aws_access_key_id=settings.get('AWS_ACCESS_KEY'),
            aws_secret_access_key=settings.get('AWS_SECRET_ACCESS_KEY'),
            region_name='us-east-1'
        )

        dynamodb = session.resource('dynamodb')
        dynamodb_index = dynamodb.Table(settings.get('DYNAMODB_CRAWLING_INDEX'))

        namespace = settings.get('USER_NAMESPACE')

        return cls(dynamodb_index, namespace)

    def process_item(self, item, spider):
        # Store the meta info in our DynamoDB index
        try:
            self.article_index.put_item(
                    Item={
                        'Namespace': self.namespace,
                        'Id': item['id'],
                        'CrawlTime': item['crawl_time'],
                        'Url': item['url'],
                        'Spider': spider.name
                    }
                )
        # according to http://stackoverflow.com/questions/16224819/dynamodb-handling-throttling-with-boto
        # boto has internal retry, thus in case of error we do not have to
        # retry
        except ClientError:
            pass

        return item

    def close_spider(self, spider):
        pass


class SaveDataToS3Pipeline(object):
    """This pipeline steps stores emitted items to an S3 bucket.

    S3 counts each request to the S3 bucket, which might lead to high
    costs if a lot of items are scraped. Thus, this class
    performs buffering and will save files with multiple items in one file
    to S3.
    """
    ITEMS_CACHE_MAXSIZE = 100

    def __init__(self, s3_data, namespace):
        self.namespace = namespace

        self.articles_data = s3_data
        self.items_cache = collections.defaultdict(list)

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        session = boto3.Session(
            aws_access_key_id=settings.get('AWS_ACCESS_KEY'),
            aws_secret_access_key=settings.get('AWS_SECRET_ACCESS_KEY'),
            region_name='us-east-1'
        )
        s3 = session.resource('s3')
        s3_data = s3.Bucket(settings.get('S3_DATA_BUCKET'))

        namespace = settings.get('USER_NAMESPACE')

        return cls(s3_data, namespace)

    def process_item(self, item, spider):
        # Store the meta info in our DynamoDB index
        try:
            self.items_cache[spider.name].append(item)
        # according to http://stackoverflow.com/questions/16224819/dynamodb-handling-throttling-with-boto
        # boto has internal retry, thus in case of error we do not have to
        # retry
        except ClientError:
            pass

        # if the items cache is large, flush it
        if len(self.items_cache[spider.name]) > self.ITEMS_CACHE_MAXSIZE:
            self._flush_cache_to_s3(spider.name)

        return item

    def close_spider(self, spider):
        # When the spider is finished, we need to flush the cache one last
        # time to make sure that all items are stored
        self._flush_cache_to_s3(spider.name)

    def _flush_cache_to_s3(self, spider_name):
        ie = self._get_exporter()

        items = self.items_cache[spider_name]

        if len(items) == 0:
            return

        file_lines = []
        for item in items:
            exported = ie.export_item(item)
            file_lines.append(json.dumps(exported))

        min_crawl_time = min([item['crawl_time'] for item in items])
        max_crawl_time = max([item['crawl_time'] for item in items])

        # store the original source to S3
        s3_key = '%s/%s/%s-to-%s.json' \
            % (self.namespace, spider_name, min_crawl_time, max_crawl_time)

        self.articles_data.put_object(Key=s3_key, Body='\n'.join(file_lines))

        self.items_cache.pop(spider_name, None)

    def _get_exporter(self, **kwargs):
        return PythonItemExporter(binary=False, **kwargs)
