# Skyscraper

Skyscraper is the scraping engine of molescrape. It can perform targeted
crawls for specific data in defined intervals.


## Documentation

The full user documentation can be found at
[docs.molescrape.com](https://docs.molescrape.com/). This README file is
designed to be a quick overview.


## Usage

There is a command line client that can be used to run crawls. For server
operation, run the following command. This will start a process that will
execute your spiders whenever required:

```bash
skyscraper
```

To run a spider manually, use

```bash
skyscraper-spider [namespace] [spider]
```

with the namespace and the name of the spider.


## Items

Each item that was crawled and should be stored and sent to postprocessing
must be emitted as a `BasicItem`.

Each item must have a unique ID for duplicate detection and the URL from which
this item was retrieved.

**Attention:** If you have multiple spiders in one namespace, almost all of the
time you want to include the spider name in the ID. Not adding the spider
name to the ID is only useful if you have to spiders that might collect
the same items and these should be detected as duplicates. I have not seen
a use case for this up to now, but wanted to keep it possible.

```json
{
    "id": "examplespider-12345",
    "url": "http://example.com/12345",
    "source": "<!DOCTYPE html><html><body>...</body></html>",
    "data": {"some-key": "some-value"},
    "crawl_time": "2018-09-29T10:18:30Z",
    "spider": "examplespider"
}
```

`id` and `url` are required and must be set by you,
`source` are `data` are optional,
and `crawl_time` and `spider` are added automatically. `crawl_time` is the
time in UTC.

Setting the `source` field is useful if you want to do additional data
extraction later. If you do all processing in your spider already, then you
probably  want to set the `data` field instead. This field can contain
arbitrary serializable python structures (e.g. lists or dictionaries).

```json
{
    "id": "examplespider-authors-harukimurakami",
    "url": "http://example.com/authors",
    "data": {"name": "Haruki Murakami", "birth": 1949},
    "crawl_time": "2018-09-29T10:18:30Z",
    "spider": "examplespider"
}
```

If you extract your elements directly in your spider, many items will probably
share the same `url`. This is allowed.

Of course, you can also combine both `data` and `source` at the same time.
This is useful, if you extract most data in your spider already, but think that
later you might have to extract some more data.


[molescrape-db]: https://github.com/molescrape/molescrape-database
