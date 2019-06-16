import json
import uuid
import os

from scrapy.exporters import PythonItemExporter


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
