import json
import datetime
import scrapy
import scrapy.squeues
import uuid
import queuelib
import psycopg2
import psycopg2.extras
import inspect

# TODO: Maybe these already do a bytes to unicode conversion, so we don't
# have to do it?
from scrapy.utils.reqser import request_to_dict, request_from_dict
from scrapy.utils.misc import load_object


class PostgresScheduler(object):
    """The PostgresScheduler is a combined in-memory and persistent
    scheduler. It will keep a maximum number of k requests in memory and
    crawl these k requests. All other requests will be stored to the
    PostgreSQL database and can be crawled later.
    """

    def __init__(self, dupefilter, conn, stats, namespace, max_process=500):
        self.df = dupefilter
        self.conn = conn
        self.stats = stats
        self.namespace = namespace

        # A maximum number of request should be processed per spider
        # in one batch
        self.MAX_PROCESS = max_process

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        connstring = settings.get('POSTGRES_CONNSTRING')
        conn = psycopg2.connect(connstring)

        dupefilter_cls = load_object(settings.get('DUPEFILTER_CLASS'))
        dupefilter = dupefilter_cls.from_settings(settings)

        batch_size = settings.get('SCHEDULER_POSTGRES_BATCH_SIZE')
        namespace = settings.get('USER_NAMESPACE')

        return cls(dupefilter,
                   conn=conn,
                   stats=crawler.stats,
                   namespace=namespace,
                   max_process=batch_size)

    def has_pending_requests(self):
        """Return true as long as the scheduler still has requests in the
        in-memory queue.
        """
        return len(self) > 0

    def open(self, spider):
        self.spider = spider
        self.mqs = queuelib.PriorityQueue(
            lambda priority: scrapy.squeues.LifoMemoryQueue())

        return self.df.open()

    def close(self, reason):
        return self.df.close(reason)

    def enqueue_request(self, request):
        if not request.dont_filter and self.df.request_seen(request):
            self.df.log(request, self.spider)
            return False

        num_enqueued = self.stats.get_value('scheduler/enqueued',
                                            default=0, spider=self.spider)
        if num_enqueued < self.MAX_PROCESS:
            self._mqpush(request)
            self.stats.inc_value('scheduler/enqueued/memory',
                                 spider=self.spider)
        else:
            self._push_postgres(request)
            self.stats.inc_value('scheduler/enqueued/disk', spider=self.spider)

        self.stats.inc_value('scheduler/enqueued', spider=self.spider)

        return True

    def next_request(self):
        additionally_dequeued = 0

        request = self.mqs.pop()

        num_processed = self.stats.get_value('scheduler/dequeued',
                                             default=0, spider=self.spider)
        if request:
            self.stats.inc_value('scheduler/dequeued/memory',
                                 spider=self.spider)
        elif num_processed < self.MAX_PROCESS:
            remaining_count = self.MAX_PROCESS - num_processed
            requests = self._get_persistent_requests(remaining_count)
            if len(requests):
                request = requests[0]

                for req in requests[1:]:
                    self.stats.inc_value('scheduler/enqueued/memory',
                                         spider=self.spider)
                    self.stats.inc_value('scheduler/enqueued',
                                         spider=self.spider)
                    self._mqpush(req)

                self.stats.inc_value('scheduler/dequeued/disk',
                                     spider=self.spider,
                                     count=len(requests))
                additionally_dequeued = len(requests) - 1
            else:
                request = None

        if request:
            self.stats.inc_value('scheduler/dequeued', spider=self.spider,
                                 count=1+additionally_dequeued)

        return request

    def __len__(self):
        return len(self.mqs)

    def _push_postgres(self, request):
        request_id = str(uuid.uuid4())
        c = self.conn.cursor()
        c.execute('''INSERT INTO skyscraper_requests
            (request_id, spider_id, priority, url, method, callback,
            errback, headers, body, cookies, meta, create_date)
            VALUES
            (
                %s,
                (
                    SELECT spider_id FROM skyscraper_spiders s
                    JOIN projects p ON s.project_id = p.project_id
                    WHERE s.name = %s AND p.name = %s
                ),
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )''',
            (
                request_id,
                self.spider.name,
                self.namespace,
                request.priority,
                request.url,
                request.method,
                self._function_to_string(request.callback),
                self._function_to_string(request.errback),
                json.dumps(self._encode_bytes_dict(request.headers)),
                request.body,
                json.dumps(self._encode_bytes_dict(request.cookies)),
                json.dumps(request.meta),
                datetime.datetime.utcnow()
            ))

        self.conn.commit()

        # TODO: Actually check for errors and return correct result
        return True

    def _mqpush(self, request):
        self.mqs.push(request, -request.priority)

    def _get_persistent_requests(self, num):
        c = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute('''SELECT request_id, priority, url, method,
                callback, errback, headers, body, cookies, meta
            FROM skyscraper_requests r
            JOIN skyscraper_spiders s ON r.spider_id = s.spider_id
            JOIN projects p ON s.project_id = p.project_id
            WHERE s.name = %s AND p.name = %s
            ORDER BY priority DESC, create_date
            LIMIT %s''',
            (self.spider.name, self.namespace, num))

        requests = []
        rows = c.fetchall()
        for res in rows:
            c.execute('''DELETE FROM skyscraper_requests
                WHERE request_id = %s''', (res[0],))

            requests.append(
                scrapy.Request(
                    res['url'],
                    priority=res['priority'],
                    method=res['method'],
                    callback=self._string_to_function(res['callback']),
                    errback=self._string_to_function(res['errback']),
                    headers=self._load_json_or_none(res['headers']),
                    body=res['body'],
                    cookies=self._load_json_or_none(res['cookies']),
                    meta=self._load_json_or_none(res['meta'])))
        self.conn.commit()

        return requests

    def _load_json_or_none(self, doc):
        if doc:
            return json.loads(doc)
        else:
            return None

    def _function_to_string(self, func):
        if func is None:
            return None
        elif isinstance(func, str):
            return func
        elif inspect.ismethod(func):
            return 'self.{}'.format(func.__name__)
        else:
            return func.__name__

    def _string_to_function(self, funcname):
        if funcname is None:
            return None
        elif 'self.' in funcname:
            methodname = funcname[5:]
            return getattr(self.spider, methodname)
        else:
            raise Exception('Non-method functions not implemented')

    def _encode_bytes_dict(self, dictionary):
        new_dict = {}
        for key, value in dictionary.items():
            key_u = key.decode('utf-8')
            if isinstance(value, list):
                value_u = self._encode_bytes_list(value)
            else:
                value_u = value.decode('utf-8')

            key_u = key.decode('utf-8')
            new_dict[key_u] = value_u

        return new_dict

    def _encode_bytes_list(self, l):
        return [v.decode('utf-8') for v in l]
