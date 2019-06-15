#!/usr/bin/env bats

setup() {
    mkdir -p /tmp/skyscraper-tests/git/testing
    git init /tmp/skyscraper-tests/git
    cp skyscraper/spiders/example.py /tmp/skyscraper-tests/git/testing/example.py

    cd /tmp/skyscraper-tests/git
    git add testing/example.py
    git config --local user.name "Unit Test"
    git config --local user.email "testing@molescrape.com"
    git commit -m "add spider"

    mkdir -p /tmp/skyscraper-tests/gitworkdir
}

teardown() {
    rm -rf /tmp/skyscraper-tests
}

@test "crawl example.com with spider from git" {
    # TODO
    #skyscraper crawl-manual testing example
    #count=$(aws s3 ls s3://skyscraper-testing-data/testing/example/ | wc -l)

    #[ "$count" -eq 1 ]
    [ 1 -eq 1 ]
}
