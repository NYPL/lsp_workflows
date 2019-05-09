# Encore and Research Catalog Log in and Log out

Workflow: [Encore and Research Catalog Log in and Log out](workflows/encore_and_research_catalog_log_in_and_log_out.md)

## READMEs of Components:

* [Header Component](https://github.com/NYPL/dgx-header-component)
* [Encore](https://bitbucket.org/NYPL/dgx-encore-custom-styling/src)
* [Reseach Catalog](https://bitbucket.org/NYPL/dgx-webpac-styling/src/master/)

## Deployments

* Header Component
  * [NYPL Header React NPM Component](https://www.npmjs.com/package/@nypl/dgx-header-component)

For Encore and Research Catalog, we use III's platform to deploy them.

* Encore
  * Prod: https://ilsstaff.nypl.org:63100/sierra/admin/SignOnPage.html
  * Test: https://nypl-sierra-test.iii.com:63100/sierra/admin/SignOnPage.html
* Research Catalog
Need to use the application III Runner to deploy the changes.

# Discovery UI Search

Workflow: [Discovery UI Search](workflows/discovery_ui_search.md)

## READMEs of Components:

* [Discovery UI](https://github.com/NYPL-discovery/discovery-front-end)
* [Patron Service](https://github.com/NYPL-discovery/patron-service)
* [Discovery API](https://github.com/NYPL-discovery/discovery-api)
* Elasticsearch Service (No repo)
* [NYPL Core](https://github.com/NYPL/nypl-core)

## AWS Deployments:

* Discovery UI
  * Prod: Elastic Beanstalk: discovery-ui-production
  * QA: Elastic Beanstalk: discovery-ui-qa
* Patron Service
  * Prod: Lambda > Functions > PatronService-production
  * QA: Lambda > Functions > PatronService-qa
* Discovery API
  * Prod: Elastic Beanstalk > discovery-api-prodcution
  * QA: Elastic Beanstalk > discovery-api-qa
* Elasticsearch Service
  * Prod: Elasticsearch Service > discovery-api-prodcution
  * QA: Elasticsearch Service > discovery-api-qa

# Patron Hold Request

Workflow: [Patron Hold Request](workflows/patron_hold_request.md)

## READMEs of Components:

* [Discovery UI](https://github.com/NYPL-discovery/discovery-front-end)
* [Patron Service](https://github.com/NYPL-discovery/patron-service)
* [Item Service](https://github.com/NYPL-discovery/itemservice)
* [Job Service](https://github.com/NYPL/job-service)
* [Hold Request Service](https://github.com/NYPL/hold-request-service)
* [Hold Request Consumer](https://github.com/NYPL/nypl-hold-request-consumer)
* [Hold Request Result Consumer](https://github.com/NYPL/hold-request-result-consumer)
* [Recap Hold Request Service](https://github.com/NYPL/recap-hold-request-service)
* [Recap Hold Request Consumer](https://github.com/NYPL/recap-hold-request-consumer)

## AWS Deployments:

* Discovery UI
  * Prod: Elastic Beanstalk: discovery-ui-production
  * QA: Elastic Beanstalk: discovery-ui-qa
* Job Service
  * Prod: Lambda > Functions > JobService-production
  * QA: Lambda > Functions > JobService-qa
* Job Service Database
  * Prod: shared-prod.frh6pg.0001.use1.cache.amazonaws.com
  * QA: shared-qa.frh6pg.0001.use1.cache.amazonaws.com
* Hold Request Service
  * Prod: Lambda > Functions > HoldRequestService-production
  * QA: Lambda > Functions > HoldRequestService-qa
* Hold Request Service Database
  * Prod: RDS > Databases > hold-requests-production
  * QA: RDS > Databases > hold-requests-qa
* Hold Request stream
  * Prod: Streams > HoldRequest-production
  * QA: Streams > HoldRequest-qa
* Hold Request Consumer
  * Prod: Lambda > Functions > HoldRequestConsumer-production
  * QA: Lambda > Functions > HoldRequestConsumer-qa
* Patron Service
  * Prod: Lambda > Functions > PatronService-production
  * QA: Lambda > Functions > PatronService-qa
* Hold Request Result stream
  * Prod: Streams > HoldRequestResult-production
  * QA: Streams > HoldRequestResult-qa
* Hold Request Result Consumer
  * Prod: Lambda > Functions > HoldRequestResultConsumer-production
  * QA: Lambda > Functions > HoldRequestResultConsumer-qa
* Recap Hold Request Service
  * Prod: Lambda > Functions > RecapHoldRequestService-production
  * QA: Lambda > Functions > RecapHoldRequestService-qa
* Recap Hold Request Stream
  * Prod: Streams > RecapHoldRequest-production
  * QA: Streams > RecapHoldRequest-qa
* Recap Hold Request Consumer
  * Prod: Lambda > Functions > RecapHoldRequestConsumer-production
  * QA: Lambda > Functions > RecapHoldRequestConsumer-qa
* AWS simple email service

## External Services:

* Sierra REST API
* NCIP AcceptItem
* SCSB API
* SCSB UI
  * prod: https://scsb.recaplib.org/
  * qa: https://uat-recap.htcinc.com/
