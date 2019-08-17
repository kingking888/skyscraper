#!/usr/bin/env bats

setup() {
    rm -rf /tmp/skyscraper-integration-tests

    pyppeteer-install

    mkdir -p /tmp/skyscraper-integration-tests/spiders
    mkdir -p /tmp/skyscraper-integration-tests/items
}

teardown() {
    rm -rf /tmp/skyscraper-integration-tests
}

@test "run skyscraper with example repository" {
    skyscraper &

    # Give the process 30 seconds for execution, then stop it
    pid=$!
    sleep 30
    kill $pid

    count_scrapy=$(ls /tmp/skyscraper-integration-tests/items/onetime_spiders/example/ | wc -l)
    count_chrome=$(ls /tmp/skyscraper-integration-tests/items/chrome_headless/example/ | wc -l)

    [ "$count_scrapy" -ge 1 ]
    [ "$count_chrome" -ge 1 ]
}

@test "crawl example.com with spider from git" {
    skyscraper-spider onetime_spiders example
    count=$(ls /tmp/skyscraper-integration-tests/items/onetime_spiders/example/ | wc -l)

    [ "$count" -eq 1 ]
}

@test "crawl example.com with Chrome headless from git" {
    skyscraper-spider chrome_headless example --engine chrome
    count=$(ls /tmp/skyscraper-integration-tests/items/chrome_headless/example/ | wc -l)

    [ "$count" -eq 1 ]
}
