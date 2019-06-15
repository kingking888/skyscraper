import os
import shutil
from zope.interface import implementer

from scrapy.interfaces import ISpiderLoader
from scrapy.utils.misc import walk_modules
from scrapy.utils.spider import iter_spider_classes

import importlib
import scrapy
import inspect
import subprocess

from skyscraper.git import DeclarativeRepository


@implementer(ISpiderLoader)
class GitSpiderLoader(object):
    """Reads spiders from a git repository"""

    def __init__(self, git_repo, namespace):
        self.git_repo = git_repo
        self.namespace = namespace

    @classmethod
    def from_settings(cls, settings):
        git_repo = DeclarativeRepository(
            settings.get('GIT_REPOSITORY'),
            settings.get('GIT_WORKDIR'),
            subfolder=settings.get('GIT_SUBFOLDER'),
            branch=settings.get('GIT_BRANCH')
        )

        namespace = settings.get('USER_NAMESPACE')

        return cls(git_repo, namespace)

    def load(self, spider_name):
        return self.git_repo.load_spider(self.namespace, spider_name)

    def find_by_request(self, request):
        pass

    def list(self):
        pass


@implementer(ISpiderLoader)
class FolderSpiderLoader(object):
    """FolderSpiderLoader reads spider code from a folder on the file system.
    The folders must be structured according to the namespaces and spider
    names. The namespace must be a folder and the spider code must be in
    a Python file with the spider name as file name:

        /path/to/folder/<namespace>/<spider-name>.py
    """

    def __init__(self, spiders_folder, namespace, spider_modules):
        self.spiders_folder = spiders_folder
        self.namespace = namespace

        self._spiders = {}
        self.spider_modules = spider_modules

    @classmethod
    def from_settings(cls, settings):
        spiders_folder = settings.get('SPIDERS_FOLDER')
        namespace = settings.get('USER_NAMESPACE')

        spider_modules = settings.getlist('SPIDER_MODULES')

        return cls(spiders_folder, namespace, spider_modules)

    def load(self, spider_name):
        self._fetch_spider_code(spider_name)

        # re-do loading spiders each time, so that we fetch also
        # the newly downloaded spider
        self._load_all_spiders()

        try:
            return self._spiders[spider_name]
        except KeyError:
            raise KeyError("Spider not found: {}".format(spider_name))

    def _fetch_spider_code(self, spider_name):
        # TODO: is it possible to get this somewhere from scrapy?
        project_folder = os.path.dirname(os.path.realpath(__file__))
        scrapy_spiders_folder = os.path.join(project_folder, 'spiders')

        source_file = os.path.join(self.spiders_folder, self.namespace, spider_name + '.py')
        target_file = os.path.join(scrapy_spiders_folder, spider_name + '.py')

        shutil.copyfile(source_file, target_file)

    def _load_spiders(self, module):
        # use the built-in function for loading spiders
        for spcls in iter_spider_classes(module):
            self._spiders[spcls.name] = spcls

    def _load_all_spiders(self):
        # TODO: Combine common code with other loaders into a common class
        for name in self.spider_modules:
            try:
                for module in walk_modules(name):
                    self._load_spiders(module)
            except ImportError as e:
                if self.warn_only:
                    msg = ("\n{tb}Could not load spiders from module '{modname}'. "
                           "See above traceback for details.".format(
                                modname=name, tb=traceback.format_exc()))
                    warnings.warn(msg, RuntimeWarning)
                else:
                    raise

    def find_by_request(self, request):
        raise NotImplementedError("find_by_request is not supported by FolderSpiderLoader")

    def list(self):
        source_folder = os.path.join(self.spiders_folder, self.namespace)

        spider_names = [f.replace('.py', '') for f in os.listdir(source_folder) \
                        if os.path.isfile(os.path.join(source_folder, f))]

        return spider_names
