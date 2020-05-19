# Tools for developing a service listening to a Kinesis Stream

## NYPL services:
1. https://github.com/NYPL-discovery/node-nypl-streams-client
2. https://github.com/NYPL/lsp_workflows/blob/d66eaeceb39401a533440420aca6004ee7c3c78f/workflows/bib-and-item-data-pipeline.md#appendix-b-re-playing-updates
3. https://github.com/NYPL-discovery/discovery-store-poster/blob/master/kinesify-data.js

Specifically for developing a Lambda listening to a Kinesis stream, using the Node NYPL Stream Client (#1 above) as described in the LSP Workflows (#2 above) is a great way to test a Lambda once it has been deployed. I found the directions really easy to follow and the command worked right away. Locally, the Lambda can be developed with mock Kinesis events. Once deployed, the stream client can be used to trigger Kinesis events for QA.

To use the `kinesify` data script (#3), clone down the `discovery-store-poster` repo, follow the instructions in its README for the `.env` file, then run this command in the command line:
```
node kinesify-data --envfile config/production.env --profile nypl-digital-dev --ids "[BIB ID]"
```

## Localstack:
* https://github.com/localstack/localstack, https://localstack.cloud/
* Tutorial: https://dev.to/goodidea/how-to-fake-aws-locally-with-localstack-27me

Localstack seems to be a more involved tool and would be good for end-to-end testing of a microservice architecture. From their description:
“LocalStack provides an easy-to-use test/mocking framework for developing Cloud applications. It spins up a testing environment on your local machine that provides the same functionality and APIs as the real AWS cloud environment.”
Their docs are underdeveloped. API Docs are “Coming soon” as of writing this assessment on May 1, 2020.
