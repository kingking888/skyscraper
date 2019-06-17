import yaml


class Configuration(object):
    def __init__(self, project, spider):
        self.project = project
        self.spider = spider
        self.recurrency_minutes = None
        self.use_tor = False
        self.enabled = False

    @classmethod
    def from_dict(cls, d):
        if 'project' not in d:
            raise YamlException('Field "project" is required in config')
        if 'spider' not in d:
            raise YamlException('Field "spider" is required in config')

        c = cls(d['project'], d['spider'])

        c.recurrency_minutes = d.get('recurrency_minutes', None)
        c.use_tor = d.get('use_tor', False)
        c.enabled = d.get('enabled', False)

        return c

    def __eq__(self, other):
        return self.project == other.project \
            and self.spider == other.spider \
            and self.recurrency_minutes == other.recurrency_minutes \
            and self.use_tor == other.use_tor

    def __hash__(self):
        return hash((self.project, self.spider, self.recurrency_minutes,
                     self.use_tor))


class YamlException(Exception):
    pass


def load(f, project, spider):
    d = yaml.safe_load(f)

    if d is None:
        d = {}

    d['project'] = project
    d['spider'] = spider

    return Configuration.from_dict(d)
