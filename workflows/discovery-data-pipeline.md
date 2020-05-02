# Discovery Data Pipeline

This workflow picks up where the [Bib & Item Data Pipeline](./bib-and-item-data-pipeline) workflow ends. It describes how data produced by that pipeline - relatively unchanged from it's source - is tapped and radically transformed to produce the DiscoveryAPI.

The [bottom half of this graph](https://docs.google.com/presentation/d/1kPUhT-JPOuniXndKWc_JEp2EY5rOPuH5ebSqYCe_438/edit#slide=id.g401dec0f26_0_128) shows how components are connected.

## DiscoveryStorePoster

The [DiscoveryStorePoster is a Node app](https://github.com/NYPL-discovery/discovery-store-poster) deployed as a Lambda.

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [DiscoveryStorePoster-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/DiscoveryStorePoster-production?tab=configuration) | Listens for updated bibs/items (from production Sierra originally). Saves extracted statements to database.  | [last 3hr logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/DiscoveryStorePoster-production;start=P3D) | [last 3hr of success/failure](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fLambda~'Errors~'FunctionName~'DiscoveryStorePoster-production~'Resource~'DiscoveryStorePoster-production~(id~'errors~stat~'Sum~color~'*23d13212))~(~'.~'Invocations~'.~'.~'.~'.~(id~'invocations~stat~'Sum~visible~false))~(~(expression~'100*20-*20100*20*2a*20errors*20*2f*20MAX*28*5berrors*2c*20invocations*5d*29~label~'Success*20rate*20*28*25*29~id~'availability~yAxis~'right~region~'us-east-1)))~region~'us-east-1~title~'Error*20count*20and*20success*20rate*20*28*25*29~yAxis~(right~(max~100))~start~'-PT3H~end~'P0D) |

The work of the poster is to inspect incoming bib and item records and process then with a "serializer", which extracts RDF-like statements from the data. It uses an extreme, flattened view of the data to maximize flexibility\*. More on the DiscoveryStore's [idiosyncratic data model can be found here](https://github.com/NYPL-discovery/discovery-store-poster/blob/master/data-model.md).

\* Originally, the "Discovery" project was supposed to include a lot more data than just catalog data. We wanted a non-rigid, extensible schema in a store that could accommodate statements about a variety of resource types from a variety of sources. The RDF-like data model implemented on Postgres was an interim measure to investing in a proper triple store.

## DiscoveryAPIIndexer

The [DiscoveryApiIndexer is a Node app](https://github.com/NYPL-discovery/discovery-api-indexer) deployed as a Lambda. (Note the deployment names have a slightly different name.)

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [DiscoveryIndexPoster-production](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/DiscoveryIndexPoster-production?tab=configuration) | Listens for updated bibids via `IndexDocument-production`, updates production Elasticsearch index | [last 3hr logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/DiscoveryIndexPoster-production;start=PT3H) | [last 3hr of success/failure](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~(metrics~(~(~'AWS*2fLambda~'Errors~'FunctionName~'DiscoveryIndexPoster-production~'Resource~'DiscoveryIndexPoster-production~(id~'errors~stat~'Sum~color~'*23d13212))~(~'.~'Invocations~'.~'.~'.~'.~(id~'invocations~stat~'Sum~visible~false))~(~(expression~'100*20-*20100*20*2a*20errors*20*2f*20MAX*28*5berrors*2c*20invocations*5d*29~label~'Success*20rate*20*28*25*29~id~'availability~yAxis~'right~region~'us-east-1)))~region~'us-east-1~title~'Error*20count*20and*20success*20rate*20*28*25*29~yAxis~(right~(max~100))~start~'-PT3H~end~'P0D)) |

The DiscoveryApiIndexer listens for updates on the `IndexDocument-` streams, which just broadcast the bib ids that have been updated. For a given id, the indexer reaches into the DiscoveryStore (a database it shares with the DiscoveryStorePoster) to retrieve all statements about the resource. This includes statements about descendant resources (i.e. items). Having retrieved all of the statements about a given id, it constructs a big JSON object, which it posts to the Elasticsearch domain that backs the DiscoveryAPI

## DiscoveryAPI

The [DiscoveryAPI is a Node app](https://github.com/NYPL-discovery/discovery-api) deployed as an Elasticbeanstalk.

| Deployment | Purpose | Logs | Health graph |
| ---------- | ------- | ---- | ------------ |
| [discovery-api-production](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/environment/dashboard?applicationName=discovery-api&environmentId=e-skxcgvtx3d) | Handles queries for production Discovery data | [last 5min logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/elasticbeanstalk/discovery-api-production/var/log/nodejs/nodejs.log;start=PT5M) | [EB health](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/environment/health?applicationName=discovery-api&environmentId=e-skxcgvtx3d) and [monitoring](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/environment/monitoring?applicationName=discovery-api&environmentId=e-skxcgvtx3d) |

### Issues

As it's a pretty thin proxy for requests to the Elasticsearch domain, issues that arise in the DiscoveryAPI are typically issues connecting to Elasticsearch. If *all* calls fail, check the logs for clues that the Elasticsearch domain can not be reached. See [these notes on how we restrict the DiscoveryAPI elasticsearch](https://github.com/NYPL/aws/blob/master/common/elasticsearch.md).

Another known issue is that fetching bibs with *lots* of items (e.g. periodicals like the NY Times) are not well accounted for in the API design and will time out. The document size is so large that the DiscoveryAPI app will spend several seconds just fetching the data out of Elasticsearch, followed by a nonzero amount of time formatting the data before returning it to the client. Either the DiscoveryAPI will time out waiting for Elasticsearch or the DiscoveryAPI caller will time out waiting for the DiscoveryAPI. This impacts the Discovery Front End: those bibs may not be viewable and/or requestable. In the future, this issue may be partially mitigated by, among other things, 1) improved API design that allows one to fetch only the first N items when requesting a bib; 2) implementing something like GraphQL, whereby all aspects of the response can be tailored by the caller; and/or 3) finding a way to stream the Elasticsearch response to the client, formatting on the fly (rather than consuming the entire Elasticsearch response before formatting it for the caller).
