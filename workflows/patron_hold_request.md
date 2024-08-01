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

   * The OnSiteHoldRequestService handles phys and edd requests for on-site items. When the incoming hold is a physical request, it uses the Sierra API to create the hold on the patron's account, and returns the response to the caller. If the incoming request is EDD, it generates a LibAnswers email with information about the request.

8. If the request is for an off-site item, the HoldRequestConsumer will forward the request to SCSB. Critiera for pushing the hold request to SCSB:
   - The request is for an off-site item (i.e. an item whose location id matches `/^rc/`)
   - The hold originated in RC (i.e. has a `pickupLocation` or is EDD). If the hold originated in SCSB, their system already knows about it so we do not need to tell them about it through the API

9. Finally, if that request was either a successful EDD request, a successful on-site request, or was /unsuccessful/, (three conditions where there is nothing more to process downstream) HoldRequestConsumer pushes the result to the HoldRequestResult event stream.
   - On the SCSB side, when a request is received:
     - SCSB changes the item's availability status to "Not Available"
     - SCSB changes the request status initially as "Processing"
     - If the request is a retrieval (not an EDD) SCSB then hits our recap/hold-requests endpoint (See item 10 below.)
     - If the request is an EDD:
       - If the item belongs to NYPL, SCSB will hit our checkout-requests endpoint to check the item out to a ["Generic EDD Patron"](https://docs.google.com/spreadsheets/d/1mr-LEQc1CZbQPEiLXuKK2UNG15tcRMuezDJofIVwH-4/edit#gid=0). We [translate the generic patron barcode](https://github.com/NYPL/checkout-request-service/blob/d181b6de2190aa5e7e57a47ceff49de0f1123326/src/Controller/CheckoutRequestController.php#L315-L333) into one of a number of different patron barcodes, randomly, to avoid hitting checkout limits on the generic cards.
       - If the item belongs to a partner, SCSB does not hit any of our hold or checkout-requests endpoints.


10. The HoldRequestResultConsumer picks up that event and emails the patron to let them know the status of their request. It also issues a `PATCH` on the hold record in the HoldRequestService to update `processed` (to `TRUE`) and `success` (to whatever the result was).

    - Note that this is the end of the line for all on-site requests as well as off-site EDD requests. There is nothing more to process.

11. For off-site phys requests, there's more to do. Moving to the bottom left, if the hold was a "retrieval" (i.e. phys, not an EDD request) we now want to make sure that it is represented in Sierra, so that a user can see their holds. SCSB initiates this process by hitting our RecapHoldRequestService, through the API Gateway again. It actually does this before it has checked if the item is available in LAS, presumably as it wants to make sure Sierra will allow the hold [which causes us some problems]. This request has the patron barcode, not id. Like the HoldRequestService, RecapHoldRequestService stores the data of the hold in its local DB, and registers an event, in this case within the RecapHoldRequest event stream. If the RecapHoldRequest call indicates a failure, SCSB marks the request status as "ILS Exception" and rollbacks the item availability status.

12. That event is picked up by the RecapHoldRequestConsumer.

13. The RecapHoldRequestConsumer will query the HoldRequestService to get information about the hold, in particular the patron id.

14. If the item on which the hold was placed is an NYPL item we can just generate a hold through the Sierra REST APIs. If however it was placed on a partner item, we will not have that item stored in Sierra, and so cannot use those APIs; in this case we have to [create an "on-the-fly"](https://github.com/NYPL/recap-hold-request-consumer/blob/6c02f95d2561fce6e6268c8a640f941f637948db/models/sierra_request.rb#L136-L141) (OTF) record (or "virtual record") using the Sierra API, and create a new patron hold on that.

15. Finally RecapHoldRequestConsumer will write an event to the HoldRequestResult, which will be picked up by the HoldRequestResultConsumer. This in turn will email the patron to let them know the hold has been placed, and also to update the request status to ‘processed’ in the HoldRequestService — also updating the JobService — as happened before for successful EDD requests.

16. In the meantime, SCSB polls the JobService to find out when Sierra has successfully placed the Hold. Once that happens it will change the request status to "Pending" and queue up a job to request the item from LAS.
    - If that LAS request is successful:
      - If it's a partner item, SCSB will place a checkout call on the owning institution. (The apparent success/failure of the checkout call has no effect on the process.)
      - If it's an NYPL item, the request status will change to "Retrieval order placed" (this is how it appears in SCSB UI anyway) and delivery will commence. On arrival, staff should find that the item has a hold (created in step 13) identifying the patron.

    - If that LAS request is not successful, SCSB will mark the request as "Exception" and roll back the hold by calling our Cancel Hold Request endpoint (The cancel process is described elsewhere.)

## Troubleshooting

All of the following use the [NYPL Data API Client](https://github.com/NYPL-discovery/node-nypl-data-api-client/).

To place a manual hold request, emulating the kind of call that the Research Catalog front-end does:

```
node bin/nypl-data-api.js post hold-requests '{ "patron": "PATRONID", "nyplSource": "sierra-nypl", "record": "11690119", "requestType": "hold", "recordType": "i", "pickupLocation": "mal", "neededBy": "2025-01-07T02:32:51Z", "numberOfCopies": "1" }'
```

To look up a hold request when you know the id:

```
node bin/nypl-data-api.js get hold-requests/id
```

To look up a hold request by patron id:

```
node bin/nypl-data-api.js get hold-requests?patron=PATRONID
```

(To get a patron id if you only know the patron barcode, use `node bin/nypl-data-api.js get patrons?barcode=BARCODE`.)

To look up a hold request by item id:

```
node bin/nypl-data-api.js get hold-requests?record=RECORDNUM
```

(To get an item id if you only know the item barcode, use `node bin/nypl-data-api.js get items?barcode=BARCODE`.)
