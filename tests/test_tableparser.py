from skyscraper.parsers import TableParser


def test_read_column():
    html = '<table><tr><th>Head1</th><th>Head2</th></tr>' \
            + '<tr><td>Value</td><td>Value2</td></tr></table>'

    parser = TableParser(html, header=0)
    assert ['Value'] == parser.column('Head1')
    assert ['Value2'] == parser.column('Head2')


def test_read_column_by_index():
    html = '<table><tr><th>Head1</th><th>Head2</th></tr>' \
            + '<tr><td>Value</td><td>Value2</td></tr></table>'

    parser = TableParser(html, header=0)
    assert ['Value'] == parser.column(0)
    assert ['Value2'] == parser.column(1)


def test_get_dataframe():
    html = '<table><tr><th>Head1</th><th>Head2</th></tr>' \
            + '<tr><td>Value</td><td>Value2</td></tr></table>'

    parser = TableParser(html, header=0)
    df = parser.get_dataframe()
    assert len(df) == 1
    assert df['Head1'].tolist() == ['Value']
