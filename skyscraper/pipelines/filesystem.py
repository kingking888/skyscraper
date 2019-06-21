import json
import uuid
import os

from scrapy.exporters import PythonItemExporter
from scrapy.exceptions import DropItem

from skyscraper.deduplication import DiskTrieDuplicatesFilter


class SaveDataToFolderPipeline(object):
    def __init__(self, folder, namespace):
        self.folder = folder
        self.namespace = namespace

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        folder = settings.get('SKYSCRAPER_STORAGE_FOLDER_PATH')
        namespace = settings.get('USER_NAMESPACE')

        return cls(folder, namespace)

    def process_item(self, item, spider):
        target_dir = os.path.join(self.folder, self.namespace, spider.name)
        os.makedirs(target_dir, exist_ok=True)

        random_id = str(uuid.uuid4())
        target_file = os.path.join(target_dir, '{}.json'.format(random_id))

        ie = self._get_exporter()
        exported = ie.export_item(item)
        with open(target_file, 'w+') as f:
            json.dump(exported, f)

        return item

    def _get_exporter(self, **kwargs):
        return PythonItemExporter(binary=False, **kwargs)


class DiskDeduplicationPipeline(object):
    """This is a pipeline step that checks whether an item has already been
    scraped before. It will store item IDs into a deduplication filter and
    check for all new items whether they are already in the filter list.
    """
    def __init__(self, duplicates_filter, namespace):
        self.namespace = namespace
        self.duplicates_filter = duplicates_filter

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        namespace = settings.get('USER_NAMESPACE')
        folder = settings.get('DISK_DEDUPLICATION_FOLDER')

        duplicates_filter = DiskTrieDuplicatesFilter(folder)
        return cls(duplicates_filter, namespace)

    def process_item(self, item, spider):
        combined_id = '{}-{}'.format(self.namespace, item['id'])
        if self.duplicates_filter.has_word(combined_id):
            raise DropItem("URL '%s' with item ID '%s' has already been crawled" % (item['url'], item['id']))
        else:
            self.duplicates_filter.add_word(combined_id)
            return item
