# NYPL Patron Hold Request Architecture

Please see diagram at: https://docs.google.com/presentation/d/1Tmb53yOUett1TLclwkUWa-14EOG9dujAyMdLzXOdOVc/edit#slide=id.g8c9198e121_0_0

This diagram shows the NYPL Library Services Platform (LSP) components involved in placing a hold request for an NYPL patron. (Partner patrons do not have holds within NYPL systems — those details are stored in SCSB (and presumably their local systems.))

The LSP is hosted in AWS and utilizes AWS features like lambdas and kinesis streams, as well as the database service, API Gateway, etc., etc. Lambdas are serverless code components, which are executed on demand; they can respond to requests through an API Gateway, or to Kinesis events. We use both in the LSP, but rely especially on Kinesis event streams.

Due to both this approach, and the circumstances under which the LSP was built, the LSP exhibits a very fine granularity microservice approach, and uses a wider than normal variety of languages (Ruby, JavaScript and PHP).

# Hold Request Process Summary

1. Starting in the top-left corner, there are two ways that hold requests can be generated on behalf of NYPL patrons. The standard way is for a hold request button to be pressed in the NYPL Shared Collection Catalog (https://nypl.org/scc) by a logged-in NYPL patron. The other way if for a SCSB user to place the hold in the SCSB UI on behalf of a specific patron. SCSB users can also place multiple requests in the SCSB UI, in which case the requests are split into individual requests before hitting API Gateway.

2. If the request originates from Discovery UI, the request will include the patron id fetched from the user’s cookie. If the request originates from SCSB, SCSB will make a request to the patron service to get the patron id from the barcode, before sending that request forward to the HoldRequestService.

3. In both cases, the action of requesting a hold be placed results in an HTTP request to the API Gateway, and thereby to the HoldRequestService. This request includes the patron id regardless of source.

4. The difference between a request being sent through the SCC and SCSB UI is that in the former case the hold request has a ‘pickup location’ (Sierra location id) and in the latter it has a ‘delivery location’ (ReCAP customer code). This becomes significant in step 5.

5. The HoldRequestService stores details of the Hold request (i.e., the patron, item, whether EDD or delivered, and if the latter a delivery location) and enters an event into the HoldRequest Kinesis stream.

6. That event is picked up by the HoldRequestConsumer, whose job it is to push the request to one of two places depending on if the item is on- or off-site.

7. If the request is for an on-site item, the HoldRequestConsumer will forward the request to the OnSiteHoldRequestService. This includes phys and edd requests. Note that requests for on-site items implicitly originated in RC since SCSB has no knowledge of our on-site items.

The OnSiteHoldRequestService handles phys and edd requests for on-site items. When the incoming hold is a physical request, it uses the Sierra API to create the hold on the patron's account, and returns the response to the caller. If the incoming request is EDD, it generates a LibAnswers email with information about the request.

8. If the request is for an off-site item, the HoldRequestConsumer will forward the request to SCSB. Critiera for pushing the hold request to SCSB:
  - The request is for an off-site item (i.e. an item whose location id matches `/^rc/`)
  - The hold originated in RC (i.e. has a `pickupLocation` or is EDD). If the hold originated in SCSB, their system already knows about it so we do not need to tell them about it through the API

In order to hit the SCSB API, the HoldRequestConsumer makes a request to the PatronService to change the patron id for the barcode

9. Finally, if that request was either a successful EDD request, a successful on-site request, or was /unsuccessful/, HoldRequestConsumer pushes the result to the HoldRequestResult event stream.

9. The HoldRequestResultConsumer picks up that event and emails the patron to let them know the status of their request. It also issues a `PATCH` on the hold record in the HoldRequestService to update `processed` (to `TRUE`) and `success` (to whatever the result was).

Note that this is the end of the line for all on-site requests as well as off-site EDD requests. There is nothing more to process.

10. For off-site phys requests, there's more to do. Moving to the bottom left, if the hold was on a physical item (i.e., not an EDD request) we now want to make sure that it is represented in Sierra, so that a user can see their holds. SCSB initiates this process by hitting our RecapHoldRequestService, through the API Gateway again. It actually does this before it has checked if the item is available in LAS, presumably as it wants to make sure Sierra will allow the hold [which causes us some problems]. This request has the patron barcode, not id. Like the HoldRequestService, RecapHoldRequestService stores the data of the hold in its local DB, and registers an event, in this case within the RecapHoldRequest event stream.

11. That event is picked up by the RecapHoldRequestConsumer.

12. The RecapHoldRequestConsumer will query the HoldRequestService to get information about the hold, in particular the patron id.

13. If the item on which the hold was placed is an NYPL item we can just generate a hold through the Sierra REST APIs. If however it was placed on a partner item, we will not have that item stored in Sierra, and so cannot use those APIs; in this case we have to use the NCIP interface, which will generate a dummy record and place a hold on that.

14. Finally RecapHoldRequestConsumer will write an event to the HoldRequestResult, which will be picked up by the HoldRequestResultConsumer. This in turn will email the patron to let them know the hold has been placed, and also to update the request status to ‘processed’ in the HoldRequestService — also updating the JobService — as happened before for successful EDD requests.

15. In the meantime, SCSB polls the JobService to find out when Sierra has successfully placed the Hold. Once that happens it will attempt to place the hold on the item in LAS. If that fails, it will make an HTTP request to RecapHoldRequestService with a Cancel Hold request. The cancel process is described elsewhere.
