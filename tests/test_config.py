import tempfile
import pytest

import skyscraper.config


def test_load_configuration_from_file():
    with tempfile.TemporaryFile() as f:
        f.write(b'project: my-project\n')
        f.write(b'spider: my-spider\n')
        f.write(b'recurrency_minutes: 60\n')
        f.write(b'use_tor: true\n')

        f.seek(0)

        config = skyscraper.config.load(f)

    assert config.project == 'my-project'
    assert config.spider == 'my-spider'
    assert config.recurrency_minutes == 60
    assert config.use_tor is True


def test_load_configuration_with_unset_values():
    with tempfile.TemporaryFile() as f:
        f.write(b'project: my-project\n')
        f.write(b'spider: my-spider\n')

        f.seek(0)

        config = skyscraper.config.load(f)

    assert config.project == 'my-project'
    assert config.spider == 'my-spider'
    assert config.recurrency_minutes is None
    assert config.use_tor is False


def test_load_configuration_with_missing_required_values():
    with tempfile.TemporaryFile() as f:
        f.write(b'spider: my-spider\n')

        f.seek(0)

        with pytest.raises(skyscraper.config.YamlException):
            skyscraper.config.load(f)
