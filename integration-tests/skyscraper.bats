#!/usr/bin/env bats

setup() {
    rm -rf /tmp/skyscraper-integration-tests

    mkdir -p /tmp/skyscraper-integration-tests/spiders
    mkdir -p /tmp/skyscraper-integration-tests/items
}

teardown() {
    rm -rf /tmp/skyscraper-integration-tests
}

@test "crawl example.com with spider from git" {
    skyscraper-spider onetime_spiders example
    count=$(ls /tmp/skyscraper-integration-tests/items/onetime_spiders/example/ | wc -l)

    [ "$count" -eq 1 ]
}
