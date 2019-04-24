# Patron Hold Request

Workflow: [Patron Hold Request](workflows/patron_hold_request.md)

READMEs of Components:

* Discovery UI https://github.com/NYPL-discovery/discovery-front-end
* Patron Service https://github.com/NYPL-discovery/patron-service
* Item Service https://github.com/NYPL-discovery/itemservice
* Job Service https://github.com/NYPL/job-service
* Hold Request Service https://github.com/NYPL/hold-request-service
* Hold Request Consumer https://github.com/NYPL/nypl-hold-request-consumer
* Hold Request Result Consumer https://github.com/NYPL/hold-request-result-consumer
* Recap Hold Request Service https://github.com/NYPL/recap-hold-request-service
* Recap Hold Request Consumer https://github.com/NYPL/recap-hold-request-consumer

AWS Deployments:

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

External Services:

* Sierra REST API
* NCIP AcceptItem
* SCSB API
* SCSB UI
  * prod: https://scsb.recaplib.org/
  * qa: https://uat-recap.htcinc.com/
