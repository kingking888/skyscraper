import datetime
import os
import json
import gzip


def oldest_file_and_date(folder):
    try:
        filepaths = [os.path.join(folder, fn) for fn in os.listdir(folder)]
        oldest_file = min(filepaths, key=os.path.getmtime)

        oldest_date = datetime.datetime.utcfromtimestamp(
            os.path.getmtime(oldest_file))

        return oldest_file, oldest_date
    except ValueError:
        return None, None


def files_in_date_range(folder, from_date, to_date_open_interval):
    relevant = []

    filepaths = [os.path.join(folder, fn) for fn in os.listdir(folder)]
    for filepath in filepaths:
        d = datetime.datetime.utcfromtimestamp(os.path.getmtime(filepath))

        if from_date <= d < to_date_open_interval:
            relevant.append(filepath)

    return relevant


def archive_old_files(directory):
    today = datetime.datetime.today()
    date_stop = datetime.datetime(today.year, today.month, 1)

    oldest_file, oldest_date = oldest_file_and_date(directory)
    while oldest_file and oldest_date < date_stop:
        month_begin = datetime.datetime(oldest_date.year, oldest_date.month, 1)
        plus_month = month_begin + datetime.timedelta(days=31)
        month_end = datetime.datetime(plus_month.year, plus_month.month, 1)

        filename = month_begin.strftime('%Y-%m.jl.gz')
        gzippath = os.path.join(directory, filename)

        relevant_files = files_in_date_range(directory, month_begin, month_end)
        with gzip.open(gzippath, 'wt') as f:
            for filepath in relevant_files:
                with open(filepath) as fin:
                    data = json.load(fin)
                    f.write(json.dumps(data) + '\n')

        for filepath in relevant_files:
            os.remove(filepath)

        oldest_file, oldest_date = oldest_file_and_date(directory)
