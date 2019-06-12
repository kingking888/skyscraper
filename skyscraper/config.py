import yaml


class Configuration(object):
    def __init__(self, project, spider):
        self.project = project
        self.spider = spider
        self.recurrency_minutes = None
        self.use_tor = False

    @classmethod
    def from_dict(cls, d):
        if 'project' not in d:
            raise YamlException('Field "project" is required in config file')
        if 'spider' not in d:
            raise YamlException('Field "spider" is required in config file')

        c = cls(d['project'], d['spider'])

        c.recurrency_minutes = d.get('recurrency_minutes', None)
        c.use_tor = d.get('use_tor', False)

        return c


class YamlException(Exception):
    pass


def load(f):
    d = yaml.safe_load(f)
    return Configuration.from_dict(d)
