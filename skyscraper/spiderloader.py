import os
import os.path
import shutil
from zope.interface import implementer

from scrapy.interfaces import ISpiderLoader
from scrapy.utils.misc import walk_modules
from scrapy.utils.spider import iter_spider_classes

import boto3
import psycopg2


@implementer(ISpiderLoader)
class S3SpiderLoader(object):
    def __init__(self, boto_session, s3_spiders_bucket, namespace, spider_modules):
        s3 = boto_session.resource('s3')

        self.spiders_bucket = s3.Bucket(s3_spiders_bucket)
        self.namespace = namespace

        self._spiders = {}
        self.spider_modules = spider_modules

    @classmethod
    def from_settings(cls, settings):
        spiders_bucket = settings.get('S3_SPIDERS_BUCKET')
        namespace = settings.get('USER_NAMESPACE')

        session = boto3.Session(
            aws_access_key_id=settings.get('AWS_ACCESS_KEY'),
            aws_secret_access_key=settings.get('AWS_SECRET_ACCESS_KEY'),
            region_name='us-east-1'
        )

        spider_modules = settings.getlist('SPIDER_MODULES')

        return cls(session, spiders_bucket, namespace, spider_modules)

    def load(self, spider_name):
        self._download_spider_code(spider_name)

        # re-do loading spiders each time, so that we fetch also
        # the newly downloaded spider
        self._load_all_spiders()

        try:
            return self._spiders[spider_name]
        except KeyError:
            raise KeyError("Spider not found: {}".format(spider_name))

    def _download_spider_code(self, spider_name):
        # TODO: is it possible to get this somewhere from scrapy?
        project_folder = os.path.dirname(os.path.realpath(__file__))
        spiders_folder = os.path.join(project_folder, 'spiders')

        # Create folder if not exists
        try:
            os.makedirs(spiders_folder)
        except OSError:
            pass

        file_key = '%s/%s' % (self.namespace, spider_name + '.py')
        local_file = os.path.join(spiders_folder, spider_name + '.py')

        self.spiders_bucket.download_file(file_key, local_file)

    def _load_spiders(self, module):
        # use the built-in function for loading spiders
        for spcls in iter_spider_classes(module):
            self._spiders[spcls.name] = spcls

    def _load_all_spiders(self):
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
        raise NotImplementedError("find_by_request is not supported by S3SpiderLoader")

    def list(self):
        prefix = '%s/' % self.namespace
        spider_objs = self.spiders_bucket.objects.filter(Prefix=prefix)

        spider_names = [obj.key.replace(prefix, '').replace('.py', '') for obj in spider_objs]
        return spider_names


@implementer(ISpiderLoader)
class PostgresSpiderLoader(object):
    def __init__(self, conn, namespace, spider_modules):
        self.conn = conn
        self.namespace = namespace

        self._spiders = {}
        self.spider_modules = spider_modules

    @classmethod
    def from_settings(cls, settings):
        connstring = settings.get('POSTGRES_CONNSTRING')
        namespace = settings.get('USER_NAMESPACE')

        conn = psycopg2.connect(connstring)

        spider_modules = settings.getlist('SPIDER_MODULES')

        return cls(conn, namespace, spider_modules)

    def load(self, spider_name):
        self._download_spider_code(spider_name)

        # re-do loading spiders each time, so that we fetch also
        # the newly downloaded spider
        self._load_all_spiders()

        try:
            return self._spiders[spider_name]
        except KeyError:
            raise KeyError("Spider not found: {}".format(spider_name))

    def _download_spider_code(self, spider_name):
        try:
            code = self._fetch_spider_code(spider_name)
            self._save_spider_file(spider_name, code)
        except KeyError:
            # ignore, because this is the same as if the file
            # would not have existed on the local hard disk
            pass

    def _save_spider_file(self, spider_name, code):
        # TODO: is it possible to get this somewhere from scrapy?
        project_folder = os.path.dirname(os.path.realpath(__file__))
        spiders_folder = os.path.join(project_folder, 'spiders')

        # Create folder if not exists
        try:
            os.makedirs(spiders_folder)
        except OSError:
            pass

        local_file = os.path.join(spiders_folder, spider_name + '.py')
        with open(local_file, 'w+') as f:
            f.write(code)

    def _fetch_spider_code(self, spider_name):
        c = self.conn.cursor()
        c.execute(
            """SELECT s.code FROM skyscraper_spiders s
            JOIN projects p ON s.project_id = p.project_id
            WHERE s.name = %s AND p.name = %s""",
            (spider_name, self.namespace))

        res = c.fetchone()
        if res is None:
            raise KeyError(
                    'Spider "%s/%s" not found'
                    % (self.namespace, spider_name))
        else:
            return res[0]

    def _load_spiders(self, module):
        # use the built-in function for loading spiders
        for spcls in iter_spider_classes(module):
            self._spiders[spcls.name] = spcls

    def _load_all_spiders(self):
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
        raise NotImplementedError("find_by_request is not supported by S3SpiderLoader")

    def list(self):
        prefix = '%s/' % self.namespace
        spider_objs = self.spiders_bucket.objects.filter(Prefix=prefix)

        spider_names = [obj.key.replace(prefix, '').replace('.py', '') for obj in spider_objs]
        return spider_names


@implementer(ISpiderLoader)
class FolderSpiderLoader(object):
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
        raise NotImplementedError("find_by_request is not supported by LocalSpiderLoader")

    def list(self):
        source_folder = os.path.join(self.spiders_folder, self.namespace)

        spider_names = [f.replace('.py', '') for f in os.listdir(source_folder) \
                        if os.path.isfile(os.path.join(source_folder, f))]

        return spider_names
