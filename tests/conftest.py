import os


def pytest_configure(config):
    # TODO: make the path flexible if possible, currently this forces us
    # to run the tests from the root folder always
    path = 'tests'
    os.environ['currpath'] = path
    return path
