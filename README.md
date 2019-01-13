# Skyscraper

Skyscraper is the scraping engine of molescrape. It can perform targeted
crawls for specific data in defined intervals.


## Documentation

The full user documentation can be found at
[docs.molescrape.com](https://docs.molescrape.com/). This README file is
designed to be a quick overview.


## Installation

### From Docker

To install skyscraper via docker just pull the container from the registry.

```bash
docker pull molescrape/skyscraper
```

The docker container already comes with a very basic default configuration.
The only missing configuration is `POSTGRES_CONNSTRING` for the
SQL database connection.

```bash
docker run --rm --env POSTGRES_CONNSTRING="host=your-host ..." skyscraper \
    crawl-manual example example
```

This command will execute the *example* spider and write the results to your
database.


## Configuration

To run skyscraper you have to specify the configuration first.

The following settings are mandatory:

```
# The connection string for psycopg2 to connect to the Postgres instance
POSTGRES_CONNSTRING = 'host=your-host dbname=your-db user=your-user'

# The spider loader that you want to use
# You might have to specify additional options depending on the chosen spider
# loader, c.f. the section about spider loaders
SPIDER_LOADER_CLASS = ''
```

Optionally, you may also configure:

```
# the minimum log level that should be displayed on stdout
SKYSCRAPER_LOGLEVEL = 'DEBUG'

# a custom user agent that you want to use for scraping
SKYSCRAPER_USER_AGENT = 'Mozilla/5.0 (compatible; Molescrape Skyscraper; ' \
                        + '+http://www.molescrape.com/)'
```


## Usage

There is a command line client that can be used to run crawls. For server
operation, run the following command from time to time:

```bash
skyscraper crawl-next-scheduled
```

This will check in the database which spider has to be executed next. It
will then run this spider and exit when finished.

If you only want to know which spider would be scheduled next without
actually running it, you can use

```bash
skyscraper show-next-scheduled
```

To run a spider manually, use

```bash
skyscraper crawl-manual [namespace] [spider]
```

with the namespace and the name of the spider.


### Monitoring

Skyscraper supports monitoring of the number of items scraped per day for
each spider. For this, you have to set a threshold for each spider and if
the spider collects less than the specified number of items there will be
a warning.

To trigger the analysis of the item count for the past day, use:

```bash
skyscraper check-item-count [--send-mail]
```

The flag `--send-mail` is optional. If you set it mails will be sent to the
owner of each spider. If it is not set you will only receive the names
of all spiders on the console.


### Docker

We provide a `Dockerfile` to create a docker container. To build the image,
execute:

```bash
docker build -t molescrape-skyscraper .
```

And then to run it:

```bash
docker run --rm molescrape-skyscraper crawl-next-scheduled
```

The docker container supports the same commands as the command line tool
`skyscraper`. If you pass no argument to the docker container the default
command `crawl-next-scheduled` will be executed.


## Items

Each item that was crawled and should be stored and sent to postprocessing
must be emitted as a `BasicItem`. Creating custom items and yielding them
is now deprecated, please use only `BasicItem`.

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
    "crawl_time": "2018-09-29T10:18:30Z",
    "spider": "examplespider"
}
```

`id`, `url` are required and must be set by you, `source` is optional
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


## Spider Loaders

You can store the code for your spiders in multiple locations. Skyscraper
includes the following spider loaders:

- Folder on hard disk
- Postgres database
- S3 bucket

To select the spider loader, set the environment variable
`SPIDER_LOADER_CLASS`.

### FolderSpiderLoader

To use the folder spider loader, you have to set the following two
environment variables:

```bash
SPIDER_LOADER_CLASS=skyscraper.spiderloader.FolderSpiderLoader
SPIDERS_FOLDER=/path/to/your/spiders/code
```

The spider folder has to contain one folder per namespace and then each folder
contains the spiders as python files. For example a valid folder structure
for the configuration above and a namespace called `my-namespace` with
spiders `myspider` and `myotherspider` would be:

```
- /path/to/your/spiders/code/my-namespace/myspider.py
- /path/to/your/spiders/code/my-namespace/myotherspider.py
```

### PostgresSpiderLoader

The postgres spider loader requires the
[molescrape-database setup][molescrape-db]. If you have setup the database
correctly, you need to define the following environment variables:

```bash
SPIDER_LOADER_CLASS=skyscraper.spiderloader.PostgresSpiderLoader
POSTGRES_CONNSTRING='host=your-host user=your-user dbname=molescrape'
```

### S3SpiderLoader

For the S3 spider loader you have to set the following environment variables:

```bash
SPIDER_LOADER_CLASS=skyscraper.spiderloader.S3SpiderLoader
S3_SPIDERS_BUCKET=your-bucket-name
AWS_ACCESS_KEY=your-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

Just like with the folder spider loader, the files have to be structured
according to namespace and spider name. For a namespace called `my-namespace`
and spiders called `myspider` and `myotherspider` the following S3 locations
would be valid:

```
- s3://your-bucket-name/my-namespace/myspider.py
- s3://your-bucket-name/my-namespace/myotherspider.py
```


[molescrape-db]: https://github.com/molescrape/molescrape-database
