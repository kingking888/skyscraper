import tempfile
import datetime
import time
import os

import skyscraper.archive


def test_archive_old_files(tmpdir):
    with tempfile.NamedTemporaryFile(dir=tmpdir) as f_1, \
            tempfile.NamedTemporaryFile(dir=tmpdir, delete=False) as f_21, \
            tempfile.NamedTemporaryFile(dir=tmpdir, delete=False) as f_22, \
            tempfile.NamedTemporaryFile(dir=tmpdir, delete=False) as f_3:

        f_1.write('{"foo": "data_1"}'.encode('utf-8'))
        f_21.write('{"foo": "data_21"}'.encode('utf-8'))
        f_22.write('{"foo": "data_22"}'.encode('utf-8'))
        f_3.write('{"foo": "data_3"}'.encode('utf-8'))
        f_1.seek(0)
        f_21.seek(0)
        f_22.seek(0)
        f_3.seek(0)

        today = datetime.datetime.today()
        this_month_file = today.strftime('%Y-%m.jl.gz')
        # use 28, because the shortest month is 28 days. Jumping 30 days back
        # we might possibly get a date from January if it's March 1st
        last_month = datetime.datetime(today.year, today.month, 15) \
            - datetime.timedelta(days=28)
        last_month_file = last_month.strftime('%Y-%m.jl.gz')
        two_months_ago = datetime.datetime(today.year, today.month, 15) \
            - datetime.timedelta(days=56)
        two_months_ago_file = last_month.strftime('%Y-%m.jl.gz')

        f_1_time = time.mktime(today.timetuple())
        f_2_time = time.mktime(last_month.timetuple())
        f_3_time = time.mktime(two_months_ago.timetuple())

        os.utime(f_1.name, (f_1_time, f_1_time))
        os.utime(f_21.name, (f_2_time, f_2_time))
        os.utime(f_22.name, (f_2_time, f_2_time))
        os.utime(f_3.name, (f_3_time, f_3_time))

        skyscraper.archive.archive_old_files(tmpdir)

        assert os.path.isfile(os.path.join(tmpdir, last_month_file))
        assert os.path.isfile(os.path.join(tmpdir, two_months_ago_file))

        assert not os.path.isfile(f_21.name)
        assert not os.path.isfile(f_22.name)
        assert not os.path.isfile(f_3.name)

        # The file from this month should still exist
        assert os.path.isfile(f_1.name)
        assert not os.path.isfile(os.path.join(tmpdir, this_month_file))
