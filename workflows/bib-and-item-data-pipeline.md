# Bib & Item Data Pipeline

The Bib & Item Data Pipeline is responsible for maintaining the Bib and Item Services as stable, up-to-date read-only proxies for data in Sierra and ReCAP. It also produces the `Bib-production` and `Item-production` Kinesis streams for those interested in listening to the bib/item updates as they happen.

[The upper half of this graph](https://docs.google.com/presentation/d/1kPUhT-JPOuniXndKWc_JEp2EY5rOPuH5ebSqYCe_438/edit#slide=id.g401dec0f26_0_128) shows how the components are connected.

## Pollers

The "pollers" are [one Java repo](https://github.com/NYPL-discovery/sierraupdatepoller) deployed four ways (for each environment) on ElasticBeanstalk:

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [sierra-bibid-poller-production](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/environment/dashboard?applicationName=Sierra-Bib-Item-Id-Pollers&environmentId=e-bxpqrcvrb8) | Fetches ids for bibs updated in last 30s from Sierra Production | [web-1.log](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/elasticbeanstalk/sierra-bibid-poller-production/var/log/web-1.log;start=PT3H) |  [last 3hr of updates/deletes](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'SierraBibRetriever-production~(label~'Records*20written*20by*20sierra*20bib*20poller)))~view~'timeSeries~stacked~true~region~'us-east-1~start~'-PT3H~end~'P0D~title~'Bib*20poller~stat~'Sum~period~300);query=~'*7bAWS*2fKinesis*2cStreamName*7d*20kinesis*20Sierra) |
| [sierra-bibid-delete-poller-production](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/environment/dashboard?applicationName=Sierra-Bib-Item-Id-Pollers&environmentId=e-bxpqrcvrb8) | Fetches ids for bibs *deleted* in last 60m from Sierra Production | [web-1.log](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/elasticbeanstalk/sierra-bibid-delete-poller-production/var/log/web-1.log;start=PT3H) | [last 3hr updates/deletes](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'SierraBibRetriever-production~(label~'Records*20written*20by*20sierra*20bib*20poller)))~view~'timeSeries~stacked~true~region~'us-east-1~start~'-PT3H~end~'P0D~title~'Bib*20poller~stat~'Sum~period~300);query=~'*7bAWS*2fKinesis*2cStreamName*7d*20kinesis*20Sierra) |
| [sierra-itemid-poller-production](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/environment/dashboard?applicationName=Sierra-Bib-Item-Id-Pollers&environmentId=e-pe2dchzeh9) | Fetches ids for items updated in last 60m from Sierra Production | [web-1.log](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/elasticbeanstalk/sierra-itemid-poller-production/var/log/web-1.log;start=PT3H) | [last 3hr updates/deletes](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'SierraItemUpdate-production~(label~'Records*20written*20by*20Sierra*20item*20pollers)))~view~'timeSeries~stacked~true~region~'us-east-1~stat~'Sum~period~300~title~'Item*20Poller);query=~'*7bAWS*2fKinesis*2cStreamName*7d*20SierraItemUpdate) |
| [sierra-itemid-delete-poller-production](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/environment/dashboard?applicationName=Sierra-Bib-Item-Id-Pollers&environmentId=e-3pmg3jmtqk) | Fetches ids for bibs *deleted* in last 60m from Sierra Production | [web-1.log](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/elasticbeanstalk/sierra-itemid-delete-poller-production/var/log/web-1.log;start=PT3H) | [last 3hr updates/deletes](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'SierraItemUpdate-production~(label~'Records*20written*20by*20Sierra*20item*20pollers)))~view~'timeSeries~stacked~true~region~'us-east-1~stat~'Sum~period~300~title~'Item*20Poller);query=~'*7bAWS*2fKinesis*2cStreamName*7d*20SierraItemUpdate) |

They operate by querying the Sierra Rest API on a fixed delay to identifiy all record identifiers that have been updated (which includes creation) or deleted since the last polling period. During peak activity, the poller may have to fetch multiple pages of updated records. (See "Appendix A" for issues with Sierra's pagination mechanism.) Each identified id is sent as an event into one of two Kinesis streams (note they are not named consistently):
 * `SierraBibRetrievalRequest-production`: Created, updated, deleted bib ids
 * `SierraItemUpdate-production`: Created, updated, deleted item ids

### Issues

The pollers are each run by a single Java thread running on a dedicated EB-provisioned EC2. If that Java thread dies for some reason, polling stops. (In retrospect, a better environment for a polling app is probably Lambda, which can be invoked by an outside scheduler; The app process should not also be responsible for scheduling polling.) You will know that polling is stopped if:
 * There is no activity in the logs for the past 5mins+
 * The [SierraBibIdPollerCode200](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:alarm/SierraBibIdPollerCode200) or [SierraItemIdPollerCode200](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:alarm/SierraItemIdPollerCode200) alarm is in an ALARM state, which will have triggered an email (via SNS topic [SierraBibIdPoller](https://console.aws.amazon.com/sns/v3/home?region=us-east-1#/topic/arn:aws:sns:us-east-1:946183545209:SierraBibIdPoller) or [SierraItemIdPoller](https://console.aws.amazon.com/sns/v3/home?region=us-east-1#/topic/arn:aws:sns:us-east-1:946183545209:SierraItemIdPoller)) as well as turning the alarm red in the [Alarm dashboard](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=Alarms-1-Hour-Period)

To restart a poller:
1. Log in to the AWS Console (account nypl-digital-dev)
1. Navigate to Elastic Beanstalk "[Sierra-Bib-Item-Id-Pollers](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/application/overview?applicationName=Sierra-Bib-Item-Id-Pollers)
1. Select the stopped poller (e.g. [sierra-bibid-poller-production](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/environment/dashboard?applicationName=Sierra-Bib-Item-Id-Pollers&environmentId=e-bxpqrcvrb8) commonly stops)
1. Select Actions > Restart App Server(s)
1. Monitor relevant logs. Note that the apps seem to spill a *lot* of concerning messages about failing to start. Give it time and space. Within five or so minutes, it should begin producing the messages you expect.

An example of a healthy invocation:

```
2019-12-23 19:12:10.587  INFO 32458 --- [://sierrapoller] o.n.h.s.processor.ResourceIdProcessor    : Current time: 2019-12-23T19:12:10Z
2019-12-23 19:12:10.587  INFO 32458 --- [://sierrapoller] o.n.h.s.processor.ResourceIdProcessor    : Calling api - https://ilsstaff.nypl.org/iii/sierra-api/v3/bibs?updatedDate=[2019-12-23T19:11:39Z,2019-12-23T19:12:10Z]&offset=0&limit=500&fields=id
2019-12-23 19:12:12.098  INFO 32458 --- [://sierrapoller] o.n.h.s.processor.ResourceIdProcessor    : Sierra api response code - 200
2019-12-23 19:12:12.098  INFO 32458 --- [://sierrapoller] o.n.h.s.processor.ResourceIdProcessor    : Sierra api response body - 
{
    "total": 13,
    "start": 0,
    "entries": [
        {
            "id": "14481212"
        },
        ...
        {
            "id": "22045578"
        }
    ]
}
2019-12-23 19:12:12.265  INFO 32458 --- [://sierrapoller] o.n.h.s.resourceid.poster.StreamPoster   : bibs : Sent 13 resources to Kinesis stream: SierraBibRetriever-production
2019-12-23 19:12:12.281  INFO 32458 --- [://sierrapoller] o.n.h.s.resourceid.poster.StreamPoster   : bibs : Sent 13 resources to Kinesis stream: SierraBibUpdate-production
2019-12-23 19:12:12.284  INFO 32458 --- [://sierrapoller] o.n.h.s.processor.CompleteCacheUpdate    : Completed updating cache
```

Another issue that can arise in the pollers is that they are operating correctly but have fallen behind. This can happen if there has been a surge of updates/deletes and they're still working to identify all of the affected ids. It can also happen following a poller outage, after which there will have been a lot of updated ids to consume. In either case, the poller will be paging through hundreds or thousands of pages of ids (in batches of 100) to acquire them all, which means recently updates in Sierra may not be represented downstream in the Bib/Item service for a while. There's not much one can do to address this as updated ids are processed in the order they have been updated; There's no way to prioritize updates for a particular item. You can only monitor the poller logs to ensure they finish paging through the backlog (i.e. the logged `updatedDate` query reflects a recent 30s range), followed by monitoring the retrievers to confirm they catch up too. In general, because they are only fetching ids - and doing so in batches of 100 - the pollers very quickly recover from a backlog issue; If pollers are confirmed running, the retrievers deserve most of the blame for stale data because they're slower to process a big backlog.

## Retrievers

The "retrievers" are [one Node repo](https://github.com/NYPL-discovery/sierra-retriever) deployed two ways (for each environment) as Lambdas:

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [SierraBibRetrieverRequest-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/SierraBibRetrieverRequest-production?tab=configuration) | Reads created/updated/deleted ids from `SierraBibRetrievalRequest-production`, fetches the whole MiJ record from Sierra, and posts the result to `BibPostRequest-production` | [log](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/SierraBibRetrieverRequest-production;start=PT3H) | [last 3hr writes](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'BibPostRequest-production~(label~'Bibs*20posted*20by*20Bib*20retriever))~(~'.~'GetRecords.IteratorAgeMilliseconds~'.~'SierraBibRetriever-production~(yAxis~'right~label~'SierraBibRetriever*20GetRecords.IteratorAgeMilliseconds)))~view~'timeSeries~stacked~true~region~'us-east-1~stat~'Sum~period~300~title~'Bib*20Retriever~start~'-PT3H~end~'P0D);query=~'*7bAWS*2fKinesis*2cStreamName*7d*20SierraBibRetriever) |
| [SierraItemRetrieverRequest-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/SierraItemRetrieverRequest-production?tab=configuration) | Reads created/updated/deleted ids from `SierraItemUpdate-production`, fetches the whole MiJ record from Sierra, and posts the result to `ItemPostRequest-production` | [log](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/SierraItemRetrieverRequest-production;start=PT3H) | [last 3hr writes](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'ItemPostRequest-production~(label~'Items*20posted*20by*20Item*20retriever))~(~'.~'GetRecords.IteratorAgeMilliseconds~'.~'SierraItemRetriever-production~(yAxis~'right~label~'SierraItemRetriever*20GetRecords.IteratorAgeMilliseconds)))~view~'timeSeries~stacked~true~region~'us-east-1~stat~'Sum~period~300~title~'Item*20Retriever~start~'-PT3H~end~'P0D);query=~'*7bAWS*2fKinesis*2cStreamName*7d*20SierraItemRetriever) |

The retrievers opterate by plucking ids off of the streams they are connected to and querying the Sierra REST API for the full Marc-in-JSON records. The resulting documents are merely POSTed to Kinesis streams:
 * `BibPostRequest-production`: Recently created, updated, deleted bib records
 * `ItemPostRequest-production`: Recently created, updated, deleted item records

### Issues

The retrievers are deployed via Lambda, so do not ever mysteriously stop running or need to be restarted. They're triggereed by writes to Kinesis streams. The only issue that arises with retrievers is they're slow compared to the pollers. This is because they fetch the full metadata for bibs and items, one record at a time.

If there's been a recent poller outage or another reason for a flood of updates, the retrievers will struggle to keep pace with the pollers. It's therefore not enough to check poller activity when investigating stale data; You should check that the relevant retriever has not fallen behind. You can check that in the "health graph" links above as "..GetRecord.IteratorAgeMilliseconds". That metric reflects the "age" in ms of the most recently consumed message in the input kinesis stream. When it's `0`, that means the retriever is processing messages on the input stream at about the rate they're being produced. When "GetRecord.IteratorAgeMilliseconds" on the input kinesis stream rises to, say, `123k`, that means the most recently processed event on the input stream was 123s old, indicating the retriever has fallen behind the pollers by about 2 minutes. In that scenario, updates made in Sierra are likely to appear in the Bib/Item service about two minutes late. There's not much you can do to speed things up. We're bound by the speed of the Sierra API and by the number of processes we allow to query the Sierra API at a given time.\*

\* Incidentally, the input kinesis streams ([SierraBibRetriever-production](https://console.aws.amazon.com/kinesis/home?region=us-east-1#/streams/details?streamName=SierraBibRetriever-production&tab=details) and [SierraItemRetriever](https://console.aws.amazon.com/kinesis/home?region=us-east-1#/streams/details?streamName=SierraItemRetriever-production&tab=details)) are each single-shard, which means only a single instance of a Lambda will ever be brought up at a time to process events. (If the kinesis stream was 3 shards, 3 different instances of `SierraBibRetrieverRequest-production` may be brought up to process events from the three shards.) The batch size on the lambdas is 100, however. And the apps themselves are Node, making asyncronous processing trivial. Thus, each retriever (bib and item) self-restricts to a max of 100 simultaneous calls to the Sierra api at a given time. We may be able to speed up the retrievers by raising this ceiling - either by increasing the number of shards on the input streams or increasing the batch size, although both will add load to Sierra.

## Posters

The "posters" are [one Node repo](https://github.com/NYPL-discovery/discovery-poster) deployed two ways (for each environment) as Lambdas:

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [BibPoster-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/BibPoster-production?tab=configuration) | Listens to `BibPostRequest-production` and POSTs them without modification to the BibService | [logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/BibPoster-production;start=PT3H) | [BibPoster errors and latency](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fLambda~'Errors~'FunctionName~'BibPoster-production~(color~'*23d62728~stat~'Sum))~(~'AWS*2fKinesis~'GetRecords.IteratorAgeMilliseconds~'StreamName~'BibPostRequest-production~(yAxis~'right~color~'*231f77b4))~(~'AWS*2fLambda~'Invocations~'FunctionName~'BibPoster-production~(stat~'Average)))~view~'timeSeries~stacked~true~region~'us-east-1~stat~'Maximum~period~300~title~'BibPoster*20health);query=~'*7bAWS*2fLambda*2cFunctionName*7d*20BibPoster) |
[ [ItemPoster-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/ItemPoster-production?tab=configuration) | Listens to `ItemPostRequest-production` and POSTs them without modification to the ItemService | [logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/ItemPoster-production;start=PT3H) | [ItemPoster health](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'GetRecords.IteratorAgeMilliseconds~'StreamName~'ItemPostRequest-production~(color~'*231f77b4~yAxis~'right))~(~'AWS*2fLambda~'Errors~'FunctionName~'ItemPoster-production~(color~'*23d62728))~(~'.~'Invocations~'.~'.))~view~'timeSeries~stacked~true~region~'us-east-1~stat~'Sum~period~300~title~'ItemPoster*20health);query=~'*7bAWS*2fLambda*2cFunctionName*7d*20ItemPoster) |

### Issues

The posters simply take data from a stream and post it to a service. They've never failed in a significant way. During times when we've had to process a big backlog from the pollers, they've not been seen to fall behind.

## BibService

The BibService is [a PHP app](https://github.com/NYPL-discovery/bibservice) deployed as a Lambda (with a Node wrapper):

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [BibService-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/BibService-production?tab=configuration) | REST endpoints for reading/writing bibs. Broadcasts all updated bibs to `Bib-production` Kinesis stream. | [logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/BibService-production;start=PT3H) | [BibService health](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fLambda~'Invocations~'FunctionName~'BibService-production~(color~'*232ca02c))~(~'.~'Errors~'.~'.~(color~'*23d62728~stat~'Maximum))~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'Bib-production~(color~'*239467bd)))~view~'timeSeries~stacked~false~region~'us-east-1~stat~'Sum~period~300~title~'BibService*20health);query=~'*7bAWS*2fKinesis*2cStreamName*7d*20Bib-production) |

### Issues

The BibService is a simple REST service. It has not had significant issues. For issues with data fetched from the BibService appearing stale, see components upstream (starting with the pollers).

## ItemService

The ItemService is [a PHP app](https://github.com/NYPL-discovery/bibservice) deployed as a Lambda (with a Node wrapper):

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [ItemService-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/ItemService-production?tab=configuration) | REST endpoints for reading/writing items. Broadcasts all updated items to `Item-production` Kinesis stream. | [logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/ItemService-production;start=PT3H) | [ItemService health](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'Item-production~(color~'*232ca02c))~(~'AWS*2fLambda~'Errors~'FunctionName~'ItemService-production~(color~'*23d62728~stat~'Maximum))~(~'.~'Invocations~'.~'.~(color~'*239467bd~yAxis~'right)))~view~'timeSeries~stacked~false~region~'us-east-1~stat~'Sum~period~300~title~'ItemService*20health);query=~'*7bAWS*2fLambda*2cFunctionName*7d*20ItemService-production) |

### Issues

The ItemService is a simple REST service. It has not had significant issues. For issues with data fetched from the ItemService appearing stale, see components upstream (starting with the pollers).

Sometimes an item will not be retrievable by barcode. If the pollers and retreivers appear in sync, another explanation is that the barcode on the item record is `null` due to a bug in the Sierra API prior to v4.1. Try fetching the item from the ItemService by id (by looking up its id in Sierra). If the record lacks a barcode (whereas one exists in Sierra), the only known workaround is to submit a trivial change in Sierra (via a member of the ILS team) to trigger the poller to refetch the updated record (hopefully will a correct serialization).

## ReCAP Harvester

The ReCAP Harvester is [a Java app](https://github.com/NYPL-discovery/recap-harvester) deployed as a Beanstalk. It's responsible for fetching updated bib & item data from our ReCAP partners.

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [nightly-recap-harvester-production](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/environment/dashboard?applicationName=Recap-Harvester&environmentId=e-pcvpyamfpn) | Logs into the HTC provided FTP site to download updated partner records | [last 3days of logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/elasticbeanstalk/nightly-recap-harvester-production/var/log/web-1.log;start=P3D) | [Metric: RecapHarvesterNotProcessingBibs-production](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(region~'us-east-1~metrics~(~(~'LogMetrics~'RecapHarvesterBibProcessed-Production~(stat~'Sum)))~view~'timeSeries~stacked~false~start~'-P7D~end~'P0D~period~86400~title~'RecapHarvesterNotProcessingBibs-production)) |

### Issues

Because it runs only nightly, it's difficult to assess the "health" of this process. When it's successful, it downloads a number of records and writes messages like "Processing bib - recap-cul 10737211" to its logs. That's the assumption of the [custom metric filter "Processing-bib-recap"](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricFilter:group=/aws/elasticbeanstalk/nightly-recap-harvester-production/var/app/current/recap-harvester/recap-logging.log), which is watched by alarm ["RecapHarvesterNotProcessingBibs-production"](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:alarm/RecapHarvesterNotProcessingBibs-production). When data points dip below 0 for a day (i.e. no log lines resembling "Processing bib - recap-" appear in the logs) the alarm passes into an ALARM state. The alarm is often triggered when there has simply been no updates - either because there has been no partner activity or because an issue within SCSB has failed to upload updates for a day.

## Bulk Export Reader (deprecated)

This [component](https://github.com/NYPL-discovery/bulk-export-reader) was produced for the launch of the data pipeline to quickly ingest a massive amount of Marc data without being constrained by Sierra API rate limits. We haven't used it since, and we're unlikely to use it again.

## General Troubleshooting

The most common thing that can go wrong is a item/bib appears stale in the Item/BibService. This has almost never been the fault of either service, so the first places to check would be upstream:

 * The pollers often stop running. See "Issues" section under Pollers to check/correct.
 * The retrievers rarely fail outright but may be slow to recover from surges in updates. See "Issues" under Retrievers for ways to check the progress.

## Appendix A: Sierra pagination issues

The Sierra API provides a way to fetch records for a given `updatedDate` range, e.g.:

`?updatedDate=[2019-11-18T02:40:18Z,2019-12-06T21:56:17Z]&limit=100`

That returns the first 100 records updated in the named range, **ordered by id**. (This can't be changed and creates trouble as we'll see.) If the number of records matching that query exceeds the per-page limit, one must paginate. The only known way to page through a large set of records is to use the `offset` and `limit` params. For illustration, imagine we're paging 5 at a time:

`?updatedDate=[2019-11-18T02:40:18Z,2019-12-06T21:56:17Z]&offset=0&limit=5`

That returns the first 5 ids updated in that range ordered by id. Suppose they are:

```
  1
  4
  5
  10
  20
```

Now you fetch the next set of ids:

`?updatedDate=[2019-11-18T02:40:18Z,2019-12-06T21:56:17Z]&offset=5&limit=5`

That should return the "page 2" set of ids updated in the same range, say:

```
  21
  25
  30
  32
  33
```

But what if - in the space between fetching the first set and fetching the second set - record 10 was updated, causing its updatedDate to change to a value outside the range originally queried. That would result in the "page 2" set of records actually being:

```
  25
  30
  32
  33
  35
```

We will have failed to be notified of record 21 because record 10 removed itself from "page 1". Essentially, we're paginating over a set of records whose membership is changing (being reduced, specifically) as we paginate.

Sierra items endpoint does not allow you to change the sort.

I can think of no way to use the Sierra API to paginate over records in a way that ensures we collect all records. The only assurance we can have that we've collected all updated ids for the queried range is if the result count is less than the specified limit.

In general, this will not be an issue because we rarely paginate over large ranges; In general, the membership of the queried range does not change. But when fetching over large ranges of multiple hundreds of thousands of records, if one of those records is updated in the course of several paginated queries, we start losing records.



