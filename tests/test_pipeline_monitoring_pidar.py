import responses
from scrapy.spiders import Spider

from skyscraper.pipelines.monitoring import PidarMonitoringPipeline


@responses.activate
def test_send_item_collected_event():
    responses.add(responses.GET, 'http://localhost/testns-spider',
                  json={'status': 'OK'})

    spider = Spider(name='spider')
    item = {
        'namespace': 'testns',
        'spider': 'spider',
    }

    pidar_pipeline = PidarMonitoringPipeline('http://localhost')
    pidar_pipeline.process_item(item, spider)

    assert len(responses.calls) == 1
