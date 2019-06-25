# SCSB Requests for Suppressed Locations

This document describes the means by which NYPL staff are able to place requests in the SCSB UI for materials and have them delivered to suppressed locations that are not available to the public/ in SCC.

## Customer Codes

HTC maintains "customer codes", which are two character strings identifying partner locations. Every item in SCSB has a single "customerCode", which can be thought of as its home location, analogous to our "holding locations". Similar to our own items' holding locations, each customer code maps to several other elligible delivery locations (which are also just customer codes). For example, many items originally stored in SASB have customer code "NA", which may be delivered to 35 other customer codes.

HTC manages customer codes and customer code changes in a big spreadsheet: https://docs.google.com/spreadsheets/d/1-6lROrDjiH5iVNGAk8l-p5qMbJ4l9zlOb5Uqx3etNJ0/edit#gid=539327819

We maintain a copy of the customer codes [in NYPL Core](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/recapCustomerCodes.csv). We also maintain a related mapping of [[sierra] locations](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/locations.csv), many of which are mapped to customer codes. This allows us to look up the customer code for a given sierra location and vice versa. To assist the latter case, we publish a specialized inverted hash relating customer codes to sierra locations as [a static json blob](https://nypl-core-objects-mapping-production.s3.amazonaws.com/by_recap_customer_code.json).

**Suppressed customer codes** (aka "suppressed locations", "suppressed stop/delivery codes") are SCSB customer codes that are not patron-facing, not available in SCC. Suppressed codes typically do not map to valid Sierra locations. They exist solely as a means to have items in ReCAP delivered to restricted, staff-only locations. The primary means by which items are retrieved from ReCAP is the hold request pipeline. Because suppressed codes do not map to a valid Sierra location, it shouldn't be possible to use the existing hold request architecture to deliver the items. In the following, we describe the special affordance made in the hold request pipeline for suppressed codes, which allows us to use the hold request architecture to deliver items to suppressed locations.

## Hold Requests in SCSB

The hold request workflow is described in the [NYPL Patron Hold Request Architecture workflow](./patron_hold_request.md) and [diagrammed](https://docs.google.com/presentation/d/1Tmb53yOUett1TLclwkUWa-14EOG9dujAyMdLzXOdOVc/edit#slide=id.g330b256cdf_0_0). For the purpose of understanding the special case of requests to suppressed locations, here's a detailed description of what happens when staff request an NYPL item to a suppressed customer code via SCSB UI:

(Note that everything in the following script also applies to requests made for non-suppressed customer codes except for the final point, 7. For suppressed locations, RecapHoldRequestConsumer skips hitting the Sierra API, closing the related job successfully as if a hold was created. For non-suppressed locations, RecapHoldRequestConsumer uses the Sierra API to create a hold and closes the related job based on the success of that call.)

1. SCSB POSTs to our hold-requests endpoint ([HoldRequestService](../index.md#hold-request-service)) data like the following:

```
{
  "patron": "5035845",
  "recordType": "i",
  "record": "16383251",
  "nyplSource": "sierra-nypl",
  "pickupLocation": "",
  "numberOfCopies": 1,
  "neededBy": "2020-06-21",
  "deliveryLocation": "OI"
}
```

2. The HoldRequestService generates a JobId using the [JobService](../index.md#job-service), saves the hold request to its database, and posts the event to the `HoldRequest` stream. That data resembles:

```
{
  "id": 426,
  "jobId": "770935d0d0522cb4fd",
  "patron": "5035845",
  "nyplSource": "sierra-nypl",
  "createdDate": "2019-06-21T12:26:11-04:00",
  "updatedDate": "2019-06-21T12:26:22-04:00",
  "success": true,
  "processed": true,
  "requestType": "hold",
  "recordType": "i",
  "record": "16383251",
  "pickupLocation": "",
  "neededBy": "2020-06-21T00:00:00-04:00",
  "numberOfCopies": 1,
  "deliveryLocation": "OI",
  "docDeliveryData": null,
  "error": null
}
```

3. The [HoldRequestConsumer](../index.md#hold-request-consumer) picks up the event and merely writes it to the `HoldRequestResult` stream (because it needn't post hold-requests to the SCSB API that originated in SCSB). The data written to the stream resembles:

```
{
  "jobId": "770935d0d0522cb4fd",
  "success": true,
  "error": null,
  "holdRequestId": 426
}
```

4. The [HoldRequestResultConsumer](../index.md#hold-request-result-consumer) picks that up and emails the user.

5. SCSB uses the id retrieved from step 2 above to build a new POST for our *other* hold-request endpoint: `recap/hold-requests`. The data POSTed resembles:

```
{
  "tracking_id": "426",
  "patronBarcode": "21111018617373",
  "itemBarcode": "33433102134263",
  "owningInstitutionId": "NYPL",
  "description": {
    "title": "[Standard NYPL restrictions apply] <<VEGSLUSKEN>>,       [RECAP]",
    "author":"Hjortland, Bertha.   ",
    "callNumber":null
  }
}
```

6. The [RecapHoldRequestService](../index.md#recap-hold-request-service) component posts the data to the RecapHoldRequest stream

7. The [RecapHoldRequestConsumer](../index.md#recap-hold-request-consumer) picks up the event. The related hold-request object is fetched via `tracking_id` ("426" in example above) for use later. [The `owningInstitutionId` in the HoldRequest event is inspected](https://github.com/NYPL/recap-hold-request-consumer/blob/08d4c29066c68693410777b236c1e227d3ccccd0/models/hold_request.rb#L65) to determine if the item belongs to NYPL or a partner institution.

 * **If item is an NYPL Item**, the component [POSTs an authenticated request](https://github.com/NYPL/recap-hold-request-consumer/blob/08d4c29066c68693410777b236c1e227d3ccccd0/models/sierra_request.rb#L57-L67) to the Sierra HTTP API (`"../patrons/{PATRONID}/holds/requests"`) to create a hold for the relevant NYPL item.
 * **If the item is a partner item**, the component [builds an NCIP AcceptItem call to create a temporary item record in Sierra](https://github.com/NYPL/recap-hold-request-consumer/blob/08d4c29066c68693410777b236c1e227d3ccccd0/models/accept_item_request.rb#L21-L38).

In both cases, the response from the Sierra API [is inspected for "success", returning a JSON object indicating success (`code` "2**") or failure (`code` "4/5**")](https://github.com/NYPL/recap-hold-request-consumer/blob/08d4c29066c68693410777b236c1e227d3ccccd0/models/request_result.rb#L126-L150).

### Quietly failing hold requests for known suppressed SCSB locations

When the item is an NYPL item, [a special check is made](https://github.com/NYPL/recap-hold-request-consumer/blob/08d4c29066c68693410777b236c1e227d3ccccd0/models/sierra_request.rb#L50-L52) to determine if the requested delivery location is among [several known "suppressed" locations](https://github.com/NYPL/recap-hold-request-consumer/blob/08d4c29066c68693410777b236c1e227d3ccccd0/models/sierra_request.rb#L15). If the location is suppressed, [the Sierra API request is entirely skipped; The component responds with `code` "204", indicating success](https://github.com/NYPL/recap-hold-request-consumer/blob/08d4c29066c68693410777b236c1e227d3ccccd0/models/sierra_request.rb#L56).

Essentially, the hold request is not created in Sierra, but the component responds as if it has been. This is done because SCSB is watching the relevant job and waiting for the job to read as succeeded before marking its own "Request" record as successful and initiating physical transfer of the item. In most cases the suppressed SCSB location doesn't have any related Sierra location, so there would be no location to use in the hold anyway. Rather we pretend that a hold has been created. NYPL staff must manually create a hold upon receipt of the item.

Note that suppressed locations are not handled for partner items. Presumably we're not in the practice of sending partner items to suppressed locations.

## Adding Suppressed Locations

When a new suppressed location is added to SCSB, there may be no Sierra location to relate it to. But in order for the hold to be processed all the way to point that the RecapHoldRequestConsumer can *pretend* it has succeeded, the suppressed location needs to be added to a few places:

### 1. Add `recapCustomerCode` and `location` entries to NYPL-Core

 i. The two-character customer code will need to be added to the [`recapCustomerCodes`](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/recapCustomerCodes.csv) mappings. (Note that `.csv` mapping changes should accompany [an equivalent `.json`](https://github.com/NYPL/nypl-core/tree/master/vocabularies/json-ld) file change. See [NYPL-Core Scripts](https://github.com/NYPL/nypl-core/tree/master/vocabularies/scripts) for help.)

 ii. A related [`locations`](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/locations.csv) mapping will also be needed so that the new customerCode appears to map to Sierra locations.

 iii. Once [tagged and merged to master](https://github.com/NYPL/nypl-core#general-workflow-for-changes), the NYPL-Core change should be published to S3 using [NYPL Core Objects](../index.md#nypl-core-objects) ([See "deploy" instructions in README](https://github.com/NYPL/nypl-core-objects#pushing-to-s3)).

[Example commit adding new "OI" suppressed customer code (for which we added fake Sierra location "lsc-oi")](https://github.com/NYPL/nypl-core/commit/73b8db69a2c18d90d0764be74dc2760b5e225b33)

### 2. Add suppressed customer code to RecapHoldRequestConsumer

Add customer code to [the array of known suppressed codes in RecapHoldRequestConsumer](https://github.com/NYPL/recap-hold-request-consumer/blob/08d4c29066c68693410777b236c1e227d3ccccd0/models/sierra_request.rb#L15) and deploy to QA.

### 3. Test in UAT UI

Assuming HTC has added the new suppressed customer code to their system, you should be able to create a new hold request in UAT UI for an NYPL item and target the suppressed location. If you've deployed NYPL Core and RecapHoldRequestConsumer (to qa at a minimum), the hold request will appear successful (even though no hold is actually created).
