# Syncing Production Data to QA

We occassionally overwrite Sierra Test with Sierra Prod. When this happens, we need to perform related syncs to downstream databases to ensure our QA systems align:
 - Bib, Item, and Holding service databases need to be manually synced to ensure they represent the data that has quietly overwritten the Sierra database
 - The DiscoveryAPI QA Elasticsearch database needs to be manually synced to ensure that it represents the data that has quietly overwritten the Bib, Item and Holding service databases.

Ideally we perform these syncs as close to each other as possible to limit the records that are updated in one system but not in the other. One order of operations that has appeared to work well is:

I. Day before the ILS sync:
  1. Staff should be informed that writes to Sierra Test are discouraged / may not be reflected in RC
  2. LSP Eng [disable Bib, Item, and Holding pollers in qa](#enabling-disabling-the-pollers)
  3. Ops syncs Bib, Item, and Holding Service dbs from production > qa
  4. (simultaneously to the Ops work above) LSP Eng copies Elastic production index over qa index
II. Day of ILS sync:
  1. Innovative kicks off the Sierra Prod > Test copy
  2. When Innovative signals Sierra Test is ready for testing, LSP Eng confirms and reenables the Bib, Item, and Holdings pollers to pick up Sierra Test changes since yesterday
  3. Within 1-2 hours, the Bib, Item, and Holding service dbs should be caught up and match the refreshed Sierra Test and associated discovery-api records also correctly indexed.

## Enabling/Disabling the Pollers

The pollers are controlled by EventBridge triggers:
 - [SierraBibUpdatePoller-qa](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/SierraBibUpdatePoller-qa?tab=configure)
 - [SierraBibDeleteUpdatePoller-qa](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/SierraBibDeleteUpdatePoller-qa?tab=configure)
 - [SierraItemUpdatePoller-qa](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/SierraItemUpdatePoller-qa?tab=configure)
 - [SierraItemDeleteUpdatePoller-qa](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/SierraItemUpdatePoller-qa?tab=configure)
 - [SierraHoldingUpdatePoller-qa](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/SierraHoldingUpdatePoller-qa?tab=configure)
 - [SierraHoldingDeleteUpdatePoller-qa](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/SierraHoldingDeleteUpdatePoller-qa?tab=configure)

To enable/disable the trigger:
 - On the Lambda page, follow Configuration > Trigger
 - Click on the EventBridge rule
 - Click Disable or Enable

## Syncing Production Elasticsearch to QA

The following describes how to copy production down to QA using logstash with no downtime.

> Note that this method took 3 days to complete the first time it was run because it had to be resumed frequently due to dropped Internet. The second time it was run it ran continuously for 10 hours.

**1. Enable access**

Ensure you have access to both domains by [adding your IP to the Access Policy for each](https://github.com/NYPL/aws/blob/master/common/elasticsearch.md#2-make-the-domain-public-restrict-by-ip). (You should revert this later.)

**2. Prepare the destination index**

Prepare the index using `index-admin prepare` to apply mapping, etc.:

```
node jobs/index-admin prepare --index resources-[YYYY-MM-DD] --profile nypl-digital-dev --envfile config/qa.env
```

**3. Logstash config**

Build an appropriate `logstash.conf`, such as:
```
input {
  elasticsearch {
    hosts => ["https://[fqdn of production domain]:443"]
    index => "resources-2018-04-09"
    docinfo => true
    query => '{ "sort": [ "uri" ], "query": { "query_string": { "query": "uri:>0" } } }'
  }
}
filter {
  mutate {
    remove_field => [ "@version", "@timestamp", "publisherLiteral" ]
  }
}
output {
  elasticsearch{
    hosts => ["https://[fqdn of qa domain:443"]
    manage_template => false
    index => "resources-[YYYY-MM-DD]"
    document_type => "%{[@metadata][_type]}"
    document_id => "%{[@metadata][_id]}"
  }
}
```

Note the input/output may need to be changed from "opensearch" to "elasticsearch" depending on whether the domain is actually AWS OpenSearch or a classic Elasticsearch domain. The 5.3 domains appear to be usable as "elasticsearch" targets even though AWS calls them opensearch - probably grandfathered access points.

Note also inclusion of "parallelPublisher" in `remove_field` to tell logstash to remove parallelPublisher when found. This was a deprecated property in favor of parallelPublisherLiteral property in any document it's 

**4. Begin the copy**

Newer versions of logstash appear to drop support for older Elasticsearch domains. See [this support matrix](https://www.elastic.co/support/matrix#matrix_compatibility). I downloaded [logstash 5.6 from here](https://www.elastic.co/downloads/past-releases/logstash-5-6-5) for use with a couple ES 5.3 domains. For newer Elasticsearch versions, you may be able to just `brew install logstash`. The [complete set of options to logstash are here](https://www.elastic.co/guide/en/logstash/current/running-logstash-command-line.html)

Execute the job:

```
LS_JAVA_OPTS="-Xms256m -Xmx2048m" logstash -f logstash.conf
```

Note: If logstash reports You may need to install opensearch input/output plugins:
```
cd /usr/local/Cellar/logstash/8.13.2/bin # Change to logstash path
./logstash-plugin install logstash-input-opensearch
```

The `LS_JAVA_OPTS` bit above invites logstash to use a reasonable amount of memory for the work it needs to do rather than fall over with a `java.lang.OutOfMemoryError` around about 7M records. A proverbial "make yourself at home" to the JVM.

Follow progress by checking index doc count via `GET https://[fqdn of qa domain]]/_cat/indices?v`

**If the pipeline fails**, you may need to kill the process via multiple `CTRL-c`s. Resume from the last indexed `uri`. Determine the last seen `uri` by POSTing the following to `{{ES_BASE_URI}}/{{ES_INDEX_NAME}}/resource/_search`

```
{
  "size": 1,
  "sort" : [
    { "uri": "desc" }
  ]
}
```

The single record returned has the last indexed `uri` (which is also the `_id` value). Once obtained, cause `logstash` to begin where you left off by editing the `query` line in your logstash conf as follows:

```
  query => '{ "sort": [ "uri" ], "query": { "query_string": { "query": "uri:>cb13752240" } } }'
```

In the above, replace "cb13752240" with your last seen `uri`. Resume logstash the same way you started it.

**5. Activate the new index**

When logstash indicates the job has completed, activate the new index:

Activate the new index for the ResearchCatalogIndexer:
 - In the AWS console, find the [`ResearchCatalogIndexer-qa](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/ResearchCAtalogIndexer-qa?tab=configuration)
 - Update the `ELASTIC_RESOURCES_INDEX_NAME` environmental variable to the new index name
 - Once you've confirmed it works, cut a PR to make the change official

Activate the new index for the QA discovery-api (to ensure the discovery-api reads from the correct index)::
 - In the AWS console, find the [`discovery-api-qa` Elasticbeanstalk app](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/environment/dashboard?applicationName=discovery-api&environmentId=e-yhuttrxfem)
 - Update the `RESOURCES_INDEX` environmental variable to the name of the new index name
 - Once you've confirmed it works, cut a PR to make the change official
