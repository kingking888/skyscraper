# -*- coding: utf-8 -*-

import json
import datetime

from scrapy.exporters import PythonItemExporter

import paho.mqtt.client as mqtt


class MqttOutputPipeline(object):
    def __init__(self, paho_client, namespace):
        self.namespace = namespace
        self.paho_client = paho_client

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        namespace = settings.get('USER_NAMESPACE')

        mqtt_host = settings.get('MQTT_HOST')
        mqtt_port = settings.get('MQTT_PORT')
        mqtt_client = mqtt.Client()
        mqtt_client.connect(mqtt_host, mqtt_port, 60)
        mqtt_client.loop_start()

        return cls(mqtt_client, namespace)

    def process_item(self, item, spider):
        ie = self._get_exporter()
        exported = ie.export_item(item)
        exported['namespace'] = self.namespace
        exported['spider'] = spider.name

        crawl_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        exported['crawl_time'] = crawl_time

        # send result to messaging queue
        payload = json.dumps(exported)
        self.paho_client.publish(
            'skyscraper/items/%s/%s' % (self.namespace, spider.name), payload)

        return item

    def _get_exporter(self, **kwargs):
        return PythonItemExporter(binary=False, **kwargs)
