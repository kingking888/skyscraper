#!/bin/bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# need to switch into the right folder, because otherwise scrapy does
# not work correctly (both Python functions from scrapy like
# get_project_settings() and CLI interface)
cd /opt/skyscraper && source env/bin/activate && skyscraper "$@"
