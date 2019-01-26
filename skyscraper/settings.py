# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


BOT_NAME = 'skyscraper'

SPIDER_MODULES = ['skyscraper.spiders']
NEWSPIDER_MODULE = 'skyscraper.spiders'

if os.environ.get('SKYSCRAPER_LOGLEVEL'):
    LOG_LEVEL = os.environ.get('SKYSCRAPER_LOGLEVEL')
else:
    LOG_LEVEL = 'DEBUG'

if os.environ.get('SKYSCRAPER_USER_AGENT'):
    USER_AGENT = os.environ.get('SKYSCRAPER_USER_AGENT')
else:
    USER_AGENT = 'Mozilla/5.0 (compatible; Molescrape Skyscraper; ' \
                 + '+http://www.molescrape.com/)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 0.1


ITEM_PIPELINES = {
    'skyscraper.pipelines.metainfo.AddNamespacePipeline': 100,
    'skyscraper.pipelines.metainfo.AddSpiderNamePipeline': 101,
    'skyscraper.pipelines.metainfo.AddCrawlTimePipeline': 102,
}

if os.environ.get('PIPELINE_USE_DUPLICATESFILTER_DYNAMODB') \
        and int(os.environ.get('PIPELINE_USE_DUPLICATESFILTER_DYNAMODB')):
    ITEM_PIPELINES['skyscraper.pipelines.aws.DoNotStoreDuplicatesPipeline'] = 200

    # should be immediately after SaveDataPipeline
    ITEM_PIPELINES['skyscraper.pipelines.aws.StoreItemToDuplicateFilterPipeline'] \
        = 301

if os.environ.get('PIPELINE_USE_OUTPUT_MQTT') \
        and int(os.environ.get('PIPELINE_USE_OUTPUT_MQTT')):
    ITEM_PIPELINES['skyscraper.pipelines.mqtt.MqttOutputPipeline'] = 210

if os.environ.get('PIPELINE_USE_OUTPUT_REDIS') \
        and int(os.environ.get('PIPELINE_USE_OUTPUT_REDIS')):
    ITEM_PIPELINES['skyscraper.pipelines.redis.RedisOutputPipeline'] = 220

if os.environ.get('PIPELINE_USE_OUTPUT_S3') \
        and int(os.environ.get('PIPELINE_USE_OUTPUT_S3')):
    ITEM_PIPELINES['skyscraper.pipelines.aws.SaveDataToS3Pipeline'] = 300

if os.environ.get('PIPELINE_USE_OUTPUT_POSTGRES') \
        and int(os.environ.get('PIPELINE_USE_OUTPUT_POSTGRES')):
    ITEM_PIPELINES['skyscraper.pipelines.postgres.SaveDataToPostgresPipeline'] = 300

if os.environ.get('PIPELINE_USE_OUTPUT_FOLDER') \
        and int(os.environ.get('PIPELINE_USE_OUTPUT_FOLDER')):
    ITEM_PIPELINES['skyscraper.pipelines.filesystem.SaveDataToFolderPipeline'] = 300
    SKYSCRAPER_STORAGE_FOLDER_PATH = os.environ.get('SKYSCRAPER_STORAGE_FOLDER_PATH')

# Item count must come shortly after the storage plugins to make sure that
# items that fail on or before storage are not counted and items that work
# on storage get counted
if os.environ.get('PIPELINE_USE_ITEMCOUNT_POSTGRES') \
        and int(os.environ.get('PIPELINE_USE_ITEMCOUNT_POSTGRES')):
    ITEM_PIPELINES['skyscraper.pipelines.postgres.CountItemsPostgresPipeline'] = 310


# Connection to PostgreSQL database
DB_CONN = os.environ.get('DB_CONN')
POSTGRES_CONNSTRING = os.environ.get('POSTGRES_CONNSTRING')

# Connection to AWS
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

SPIDER_LOADER_CLASS = os.environ.get('SPIDER_LOADER_CLASS')
SPIDERS_FOLDER = os.environ.get('SPIDERS_FOLDER')

S3_SPIDERS_BUCKET = os.environ.get('S3_SPIDERS_BUCKET')
S3_DATA_BUCKET = os.environ.get('S3_DATA_BUCKET')
DYNAMODB_CRAWLING_INDEX = os.environ.get('DYNAMODB_CRAWLING_INDEX')
DYNAMODB_CRAWLING_OPTIONS = os.environ.get('DYNAMODB_CRAWLING_OPTIONS')

MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_USER = os.environ.get('MAIL_USER')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_FROM = 'noreply@molescrape.com'
MAIL_TEMPLATE_BUCKET = os.environ.get('MAIL_TEMPLATE_BUCKET')
MAIL_TEMPLATE_PREFIX = os.environ.get('MAIL_TEMPLATE_PREFIX')

# Overwrite default scheduler if defined by user
if os.environ.get('SCHEDULER'):
    SCHEDULER = os.environ.get('SCHEDULER')
    SCHEDULER_REDIS_QUEUE_HOST = os.environ.get('SCHEDULER_REDIS_QUEUE_HOST')
    SCHEDULER_REDIS_BATCH_SIZE = \
        int(os.environ.get('SCHEDULER_REDIS_BATCH_SIZE'))
    SCHEDULER_POSTGRES_BATCH_SIZE = \
        int(os.environ.get('SCHEDULER_POSTGRES_BATCH_SIZE'))

PIDAR_URL = os.environ.get('PIDAR_URL')
