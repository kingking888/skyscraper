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

if os.environ.get('SKYSCRAPER_PIPELINE_USE_DUPLICATESFILTER_DISK') \
        and int(os.environ.get('SKYSCRAPER_PIPELINE_USE_DUPLICATESFILTER_DISK')):
    ITEM_PIPELINES['skyscraper.pipelines.filesystem.DiskDeduplicationPipeline'] = 200

    DISK_DEDUPLICATION_FOLDER = os.environ.get('SKYSCRAPER_DISK_DEDUPLICATION_FOLDER')

if os.environ.get('SKYSCRAPER_PIPELINE_USE_DUPLICATESFILTER_DYNAMODB') \
        and int(os.environ.get('SKYSCRAPER_PIPELINE_USE_DUPLICATESFILTER_DYNAMODB')):
    ITEM_PIPELINES['skyscraper.pipelines.aws.DoNotStoreDuplicatesPipeline'] = 200

    # should be immediately after SaveDataPipeline
    ITEM_PIPELINES['skyscraper.pipelines.aws.StoreItemToDuplicateFilterPipeline'] = 301

if os.environ.get('SKYSCRAPER_PIPELINE_USE_OUTPUT_FOLDER') \
        and int(os.environ.get('SKYSCRAPER_PIPELINE_USE_OUTPUT_FOLDER')):
    ITEM_PIPELINES['skyscraper.pipelines.filesystem.SaveDataToFolderPipeline'] = 300
    SKYSCRAPER_STORAGE_FOLDER_PATH = os.environ.get('SKYSCRAPER_STORAGE_FOLDER_PATH')

if os.environ.get('SKYSCRAPER_CHROME_NO_SANDBOX'):
    SKYSCRAPER_CHROME_NO_SANDBOX = bool(os.environ.get('SKYSCRAPER_CHROME_NO_SANDBOX'))
else:
    SKYSCRAPER_CHROME_NO_SANDBOX = False

# Connection to AWS
AWS_ACCESS_KEY = os.environ.get('SKYSCRAPER_AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('SKYSCRAPER_AWS_SECRET_ACCESS_KEY')

if os.environ.get('SKYSCRAPER_SPIDER_LOADER_CLASS'):
    SPIDER_LOADER_CLASS = os.environ.get('SKYSCRAPER_SPIDER_LOADER_CLASS')
else:
    SPIDER_LOADER_CLASS = 'skyscraper.spiderloader.GitSpiderLoader'

DYNAMODB_CRAWLING_INDEX = os.environ.get('SKYSCRAPER_DYNAMODB_CRAWLING_INDEX')
DYNAMODB_CRAWLING_OPTIONS = os.environ.get('SKYSCRAPER_DYNAMODB_CRAWLING_OPTIONS')

GIT_REPOSITORY = os.environ.get('SKYSCRAPER_GIT_REPOSITORY')
GIT_WORKDIR = os.environ.get('SKYSCRAPER_GIT_WORKDIR')
GIT_SUBFOLDER = os.environ.get('SKYSCRAPER_GIT_SUBFOLDER')
GIT_BRANCH = os.environ.get('SKYSCRAPER_GIT_BRANCH')
