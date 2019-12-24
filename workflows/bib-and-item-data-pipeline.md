# Bib & Item Data Pipeline

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

## Retrievers

The "retrievers" are [one Node repo](https://github.com/NYPL-discovery/sierra-retriever) deployed two ways (for each environment) as Lambdas:

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [SierraBibRetrieverRequest-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/SierraBibRetrieverRequest-production?tab=configuration) | Reads created/updated/deleted ids from `SierraBibRetrievalRequest-production`, fetches the whole MiJ record from Sierra, and posts the result to `BibPostRequest-production` | [log](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/SierraBibRetrieverRequest-production;start=PT3H) | [last 3hr writes](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'BibPostRequest-production~(label~'Bibs*20posted*20by*20Bib*20retriever)))~view~'timeSeries~stacked~true~region~'us-east-1~stat~'Sum~period~300~title~'Bib*20Retriever~start~'-PT3H~end~'P0D);query=~'*7bAWS*2fKinesis*2cStreamName*7d*20bib) |
| [SierraItemRetrieverRequest-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/SierraItemRetrieverRequest-production?tab=configuration) | Reads created/updated/deleted ids from `SierraItemUpdate-production`, fetches the whole MiJ record from Sierra, and posts the result to `ItemPostRequest-production` | [log](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/SierraItemRetrieverRequest-production;start=PT3H) | [last 3hr writes](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'ItemPostRequest-production~(label~'Items*20posted*20by*20Item*20retriever)))~view~'timeSeries~stacked~true~region~'us-east-1~stat~'Sum~period~300~title~'Item*20Retriever);query=~'*7bAWS*2fKinesis*2cStreamName*7d*20ItemPost) |

The retrievers opterate by plucking ids off of the streams they are connected to and querying the Sierra REST API for the full Marc-in-JSON records. The resulting documents are merely POSTed to Kinesis streams:
 * `BibPostRequest-production`: Recently created, updated, deleted bib records
 * `ItemPostRequest-production`: Recently created, updated, deleted item records

## Posters

The "posters" are [one Node repo](https://github.com/NYPL-discovery/discovery-poster) deployed two ways (for each environment) as Lambdas:

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [BibPoster-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/BibPoster-production?tab=configuration) | Listens to `BibPostRequest-production` and POSTs them without modification to the BibService | [logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/BibPoster-production;start=PT3H) | [BibPoster errors and latency](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fLambda~'Errors~'FunctionName~'BibPoster-production~(color~'*23d62728~stat~'Sum))~(~'AWS*2fKinesis~'GetRecords.IteratorAgeMilliseconds~'StreamName~'BibPostRequest-production~(yAxis~'right~color~'*231f77b4))~(~'AWS*2fLambda~'Invocations~'FunctionName~'BibPoster-production~(stat~'Average)))~view~'timeSeries~stacked~true~region~'us-east-1~stat~'Maximum~period~300~title~'BibPoster*20health);query=~'*7bAWS*2fLambda*2cFunctionName*7d*20BibPoster) |
[ [ItemPoster-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/ItemPoster-production?tab=configuration) | Listens to `ItemPostRequest-production` and POSTs them without modification to the ItemService | [logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/ItemPoster-production;start=PT3H) | [ItemPoster health](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'GetRecords.IteratorAgeMilliseconds~'StreamName~'ItemPostRequest-production~(color~'*231f77b4~yAxis~'right))~(~'AWS*2fLambda~'Errors~'FunctionName~'ItemPoster-production~(color~'*23d62728))~(~'.~'Invocations~'.~'.))~view~'timeSeries~stacked~true~region~'us-east-1~stat~'Sum~period~300~title~'ItemPoster*20health);query=~'*7bAWS*2fLambda*2cFunctionName*7d*20ItemPoster) |

## BibService

The BibService is [a PHP app](https://github.com/NYPL-discovery/bibservice) deployed as a Lambda (with a Node wrapper):

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [BibService-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/BibService-production?tab=configuration) | REST endpoints for reading/writing bibs. Broadcasts all updated bibs to `Bib-production` Kinesis stream. | [logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/BibService-production;start=PT3H) | [BibService health](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fLambda~'Invocations~'FunctionName~'BibService-production~(color~'*232ca02c))~(~'.~'Errors~'.~'.~(color~'*23d62728~stat~'Maximum))~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'Bib-production~(color~'*239467bd)))~view~'timeSeries~stacked~false~region~'us-east-1~stat~'Sum~period~300~title~'BibService*20health);query=~'*7bAWS*2fKinesis*2cStreamName*7d*20Bib-production) |

## ItemService

The ItemService is [a PHP app](https://github.com/NYPL-discovery/bibservice) deployed as a Lambda (with a Node wrapper):

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [ItemService-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/ItemService-production?tab=configuration) | REST endpoints for reading/writing items. Broadcasts all updated items to `Item-production` Kinesis stream. | [logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/ItemService-production;start=PT3H) | [ItemService health](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fKinesis~'PutRecords.Records~'StreamName~'Item-production~(color~'*232ca02c))~(~'AWS*2fLambda~'Errors~'FunctionName~'ItemService-production~(color~'*23d62728~stat~'Maximum))~(~'.~'Invocations~'.~'.~(color~'*239467bd~yAxis~'right)))~view~'timeSeries~stacked~false~region~'us-east-1~stat~'Sum~period~300~title~'ItemService*20health);query=~'*7bAWS*2fLambda*2cFunctionName*7d*20ItemService-production) |


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



