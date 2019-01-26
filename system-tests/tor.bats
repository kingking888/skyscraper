#!/usr/bin/env bats
#
setup() {
    mkdir /tmp/skyscraper-data
}

teardown() {
    rm -r /tmp/skyscraper-data
}

@test "check that TOR-enabled container has different IP from host" {
    hostip=$(curl https://api.ipify.org/)

    docker run --rm --env TOR_ENABLED=1 \
        -v $PWD/system-tests/spiders:/opt/skyscraper-spiders \
        -v /tmp/skyscraper-data:/opt/skyscraper-data \
        molescrape/skyscraper crawl-manual tor ipcheck --use-tor

    containerip=$(jq -r '.source' /tmp/skyscraper-data/*.json)

    [ "$hostip" != "$containerip" ]
}
