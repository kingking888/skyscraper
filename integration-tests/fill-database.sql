INSERT INTO projects (name)
VALUES ('test-database');

INSERT INTO skyscraper_spiders
(name, project_id, code, recurrency_minutes, next_scheduled_runtime)
VALUES (
    'test-db-spider',
    (SELECT project_id FROM projects WHERE name = 'test-database'),
    'import scrapy
from skyscraper.items import BasicItem

class ExampleSpider(scrapy.Spider):
    name = ''test-db-spider''
    allowed_domains = [''example.com'']
    start_urls = [''http://example.com/'']

    def parse(self, response):
        item = BasicItem()
        item[''id''] = ''example.com-indexpage''
        item[''url''] = response.url
        item[''slug''] = response.url.split(''/'')[-1]
        item[''source''] = response.text
        return item',
    60,
    NOW()),
(
    'unscheduled-spider',
    (SELECT project_id FROM projects WHERE name = 'test-database'),
    '# do nothing',
    NULL,
    NULL);
