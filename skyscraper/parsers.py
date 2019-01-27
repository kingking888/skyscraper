import pandas as pd


class TableParser(object):
    """This is a parser that helps in parsing a standard HTML table."""
    def __init__(self, html, header=None):
        self.table = pd.read_html(html, header=header)[0]

    def column(self, col_name):
        """Retrieve the values for a given column. The column can be either
        defined by the name (which is extracted from the table header) or
        by the column index (integer number).
        """
        if isinstance(col_name, int):
            return self.table.iloc[:, col_name].tolist()
        else:
            return self.table[col_name].tolist()

    def get_dataframe(self):
        """Get the internal pandas DataFrame."""
        return self.table
