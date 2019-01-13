#!/usr/bin/env bats

setup() {
    aws s3 rm --recursive s3://skyscraper-testing-data/test-database/
    psql -U postgres -h postgres -d molescrape -f integration-tests/fill-database.sql
}

teardown() {
    aws s3 rm --recursive s3://skyscraper-testing-data/test-database/
    psql -U postgres -h postgres -d molescrape -f integration-tests/clear-database.sql
}

@test "crawl example.com with spider from database and store to S3" {
    skyscraper crawl-next-scheduled
    count=$(aws s3 ls s3://skyscraper-testing-data/test-database/test-db-spider/ | wc -l)

    [ "$count" -eq 1 ]
}

@test "check next runtime is increased after a run" {
    before=$(skyscraper show-next-scheduled)
    skyscraper crawl-next-scheduled
    after=$(skyscraper show-next-scheduled)

    [ "$before" == "Next spider is test-database/test-db-spider." ]
    [ "$after" == "No spider is scheduled for execution." ]
}

@test "check item count is written to postgres" {
    export PIPELINE_USE_ITEMCOUNT_POSTGRES=1
    skyscraper crawl-manual test-database test-db-spider

    today="$(date +'%Y-%m-%d')"
    count=$(psql -qtA -U postgres -h postgres -d molescrape -c "SELECT items_scraped_count FROM skyscraper_spiders_stats_daily WHERE spider_id = (SELECT spider_id FROM skyscraper_spiders s JOIN projects p ON s.project_id = p.project_id WHERE p.name = 'test-database' AND s.name = 'test-db-spider') AND stats_date = '"$today"';")

    echo $count
    [ "$count" -eq 1 ]
}
