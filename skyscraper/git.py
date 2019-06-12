import os
import subprocess
import importlib
import inspect
import scrapy
import logging
import yaml


class DeclarativeRepository(object):
    def __init__(self, repo_path, workdir, branch='master'):
        self.repo_path = repo_path
        self.workdir = workdir
        self.branch = branch

        print(repo_path)
        print(workdir)

        self._update_repo()

    def iterate_spiders(self, project=None):
        """Iterates all spiders and yields pairs of (project, spider)"""

        if project is None:
            for project in self._iterate_project_folders(self.workdir):
                for project, spider in self.iterate_spiders(project):
                    yield project, spider
        else:
            project_dir = os.path.join(self.workdir, project)
            for filename in next(os.walk(project_dir))[2]:
                spider = os.path.splitext(filename)[0]

                if self._validate_spider(project, spider):
                    yield (project, spider)

    def get_config(self, project, spider):
        configfile = os.path.join(self.workdir, project, spider + '.yml')

        with open(configfile, 'r') as f:
            return yaml.safe_load(f)

    def load_spider(self, project, spider):
        spiderfile = os.path.join(self.workdir, project, spider + '.py')

        spec = importlib.util.spec_from_file_location(
            'skyscraper.spiders.{}.{}'.format(project, spider), spiderfile)
        dynamicspider = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(dynamicspider)
        except FileNotFoundError:
            raise KeyError('Spider not found: {}/{}'.format(project, spider))

        # extract the first class that is a child of scrapy.Spider
        for name, obj in inspect.getmembers(dynamicspider):
            if inspect.isclass(obj) and issubclass(obj, scrapy.Spider):
                if obj.name != spider:
                    logging.warn('Name attribute of spider {}/{} does not '
                                 + 'match its file name')
                else:
                    return obj

        raise KeyError(
            'Spider not found: {}/{}'.format(project, spider))

    def _validate_spider(self, project, spider):
        # TODO: Implement
        return True

    def _update_repo(self):
        # TODO: Check if was already cloned
        subprocess.call(['git', 'clone', self.repo_path, self.workdir])

        subprocess.call(['git', 'checkout', self.branch], cwd=self.workdir)
        subprocess.call(['git', 'pull'], cwd=self.workdir)

    def _iterate_project_folders(self, directory):
        for candidate in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, candidate)) \
                    and candidate != '.git':

                yield candidate
