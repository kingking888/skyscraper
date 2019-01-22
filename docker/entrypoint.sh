#!/bin/bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# if tor is enabled, start required services in background
if [ "$TOR_ENABLED" -eq "1" ]; then
    tor --runasdaemon 1
    # TODO: How can we reliably check when TOR is up?
    sleep 10
    privoxy /etc/privoxy/config

    export http_proxy=http://127.0.0.1:8118
    export https_proxy=https://127.0.0.1:8118
fi

# need to switch into the right folder, because otherwise scrapy does
# not work correctly (both Python functions from scrapy like
# get_project_settings() and CLI interface)
cd /opt/skyscraper && source env/bin/activate && skyscraper "$@"
