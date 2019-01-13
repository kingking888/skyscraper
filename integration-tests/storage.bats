#!/usr/bin/env bats

setup() {
    aws s3 rm --recursive s3://skyscraper-testing-data/testing/
}

teardown() {
    aws s3 rm --recursive s3://skyscraper-testing-data/testing/
}

@test "crawl example.com and store to S3" {
    skyscraper crawl-manual testing example
    count=$(aws s3 ls s3://skyscraper-testing-data/testing/example/ | wc -l)

    [ "$count" -eq 1 ]
}
