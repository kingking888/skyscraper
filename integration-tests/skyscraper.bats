#!/usr/bin/env bats

setup() {
    rm -rf /tmp/skyscraper-integration-tests

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

    count=$(ls /tmp/skyscraper-integration-tests/items/onetime_spiders/example/ | wc -l)
    [ "$count" -ge 1 ]
}

@test "crawl example.com with spider from git" {
    skyscraper-spider onetime_spiders example
    count=$(ls /tmp/skyscraper-integration-tests/items/onetime_spiders/example/ | wc -l)

    [ "$count" -eq 1 ]
}
