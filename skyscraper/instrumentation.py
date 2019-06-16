import os
import prometheus_client

import skyscraper.settings


NUMBER_OF_FILES = prometheus_client.Gauge(
    'skyscraper_num_files',
    'Number of files stored in Skyscraper',
    ['project', 'spider'])


def instrument_num_files():
    directory = skyscraper.settings.SKYSCRAPER_STORAGE_FOLDER_PATH

    for project in os.listdir(directory):
        project_dir = os.path.join(directory, project)

        if os.path.isdir(project_dir):
            for spider in os.listdir(project_dir):
                spider_dir = os.path.join(project_dir, spider)

                if os.path.isdir(spider_dir):
                    num_files = len([name for name in os.listdir(spider_dir)
                                     if os.path.isfile(os.path.join(spider_dir, name))])
                    NUMBER_OF_FILES.labels(project=project, spider=spider) \
                        .set(num_files)
