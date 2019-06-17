import tempfile

from skyscraper.deduplication import DiskTrieDuplicatesFilter


def test_duplicate_detection():
    triedir = tempfile.mkdtemp()

    f = DiskTrieDuplicatesFilter(triedir)
    f.add_word('foo')
    f.add_word('bar')

    assert not f.has_word('foobar')
    assert not f.has_word('baz')
    assert f.has_word('bar')
    assert f.has_word('foo')
