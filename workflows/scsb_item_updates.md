# SCSB Item Updates

A subset of items in NYPL's catalog are stored offsite at ReCAP and inventoried by a system called SCSB. For those items, SCSB is the authority for an item's location & status. SCSB also stores bibliographic data for those items. This document describes the process by which our ILS is kept in sync with SCSB for item status and data.

[Accompanying diagram](diagrams/scsb_item_updates.png) ([and source](https://www.lucidchart.com/documents/edit/1b9817ba-4c5a-4673-9eeb-c53ced06f163/0?driveId=0ABeXoTO8OPLWUk9PVA&beaconFlowId=DC8794CCCFF3616B))

## I. Syncing Status: Propagating Checkouts from SCSB to Sierra

SCSB calls our checkout-requests endpoint any time an item in their care is checked out to a partner or NYPL patron. Sierra doesn't *need* to know about the status change, but it's useful to know *within* Sierra an item's status in SCSB. Note that a checkout changes an item's status and is treated the same as any other metadata update.

## II. Syncing Metadata: Propagating Metadata from Sierra to SCSB

Metadata updates are propagated from our ILS to SCSB via both automatic and manual means. In both cases the actual update is managed by a component consuming a "sierra-updates-for-scsb" SQS. The following describes the two ways that SQS can be populated.

### Automatic creation of Sierra-Updates-For-SCSB Jobs

[SyncItemMetadataToSCSBListener](https://github.com/NYPL/sync-item-metadata-to-scsb-listener) listens on Bib & Item kinesis streams (representing all updates to bibs and items) to create sierra-update-for-scsb jobs.

*For each item*, the component determines if it's an item stored in ReCAP [based on the item's location](https://github.com/NYPL/sync-item-metadata-to-scsb-listener/blob/0c7470aa39cd4c53313c3d70fa074f5688f4c34c/lib/item_handler.rb#L8). If the item is determined to be in ReCAP, [it determines whether the data should be processed as an "update" (modified metadata) or a "transfer" (changed bib ownership)](https://github.com/NYPL/sync-item-metadata-to-scsb-listener/blob/0c7470aa39cd4c53313c3d70fa074f5688f4c34c/lib/item_handler.rb#L54-L57). Having made that determination, it writes the resulting job to the [SyncItemMetadataToSCSBService](https://github.com/NYPL/sync-item-metadata-to-scsb-service/), e.g.:

```
{ "barcodes": [ "123456" ], "user_email": "[registered email to send errors to]@nypl.org", "action": "update", "source": "bib-item-store-update" }
```

Note the "source" property identifies this update job as originating from an organic update in the ItemService. (This is a helpful hint downstream when handling the update as it indicates the relevant data has already been persisted to the ItemService at the time the SQS update job was written.)

If the update is determined to be a "transfer" (i.e. item assigned a new bibid), it may look like this:

```
{ "barcodes": [ "123456" ], "user_email": "[registered email to send errors to]@nypl.org", "action": "transfer", "bib_record_number": "newbibnum", "source": "bib-item-store-update" }
```

*For each bib*, the component determines if it's a bib _potentially_ with items stored in ReCAP based on whether 1) its first item is research, or 2) it's a known mixed-bib (a bib with both research and branch items). In either case, the bib definitely *might* have items in ReCAP. (We make these initial checks to avoid querying the SCSB api unnecessarily.) Having made that determination we [query SCSB api](https://github.com/NYPL/sync-item-metadata-to-scsb-listener/blob/c4c24fa33927095d540a7ebe4cbebf9183c0baef/lib/bib_handler.rb#L101) for all barcodes by bibid to verify they actually exist there.

See [Appendix A: SCSB API Search](#appendix-scsb-api-search) for sample requests & responses.

If the SCSB API returns any barcodes we pass those on to the [SyncItemMetadataToSCSBService](https://github.com/NYPL/sync-item-metadata-to-scsb-service/) as "update" jobs, e.g.:

```
{ "barcodes": [ "123456", "6789" ], "user_email": "[registered email to send errors to]@nypl.org", "action": "update" }
```

### SyncItemMetadataService: Centralizing creation of Sierra-Updates-For-SCSB jobs

The [SyncItemMetadataService](https://github.com/NYPL/sync-item-metadata-to-scsb-service/) validates and writes incoming jobs to a "sierra-updates-for-scsb" SQS.

An acceptable incoming "update" job might look like this ("action" defaults to "update"):

```
{ "barcodes": [ "123456" ], "user_email": "staff-email@nypl.org" }
```

An acceptable incoming "transfer" job might look like this:

```
{ "barcodes": [ "123456" ], "user_email": "staff-email@nypl.org", "action": "transfer": "transfer", "bib_record_number": "newbibnum" }
```

After [validation](https://github.com/NYPL/sync-item-metadata-to-scsb-service/blob/31e4553823f766a68ac87cb4f5f9d2aaa6946b14/lib/message.rb#L11), and [a slight reformatting](https://github.com/NYPL/sync-item-metadata-to-scsb-service/blob/31e4553823f766a68ac87cb4f5f9d2aaa6946b14/lib/message.rb#L31-L45), SyncItemMetadataService [writes the payload](https://github.com/NYPL/sync-item-metadata-to-scsb-service/blob/31e4553823f766a68ac87cb4f5f9d2aaa6946b14/lib/sqs_client.rb#L23-L33) to the [configured SQS endpoint](https://github.com/NYPL/sync-item-metadata-to-scsb-service/blob/31e4553823f766a68ac87cb4f5f9d2aaa6946b14/lib/sqs_client.rb#L7).

The record written to SQS resembles:

Update:
```
{ "barcodes": [ "123456" ], "user_email": "staff-email@nypl.org", "action": "update", "protectCGD": false }
```

Transfer:
```
{ "barcodes": [ "123456" ], "user_email": "staff-email@nypl.org", "action": "transfer": "transfer", "bibRecordNumber": "newbibnum", "protectCGD": true }
```

### Manual creation of Sierra-Updates-For-SCSB Jobs

The other method for populating the sierra-updates-for-scsb SQS is [SCSBuster](https://github.com/NYPL/scsbuster).

SCSBuster allows:

 * *Updates*: One can [manually queue "update" SQS jobs](http://scsbuster.nypl.org/update_metadata) by barcode(s)
 * *Transfer*: One can [manually queue "transfer" SQS jobs](http://scsbuster.nypl.org/transfer_metadata) by barcode (and destination bibid)
 * *Refile*: One can [manually call "refile" and view a log of refile errors](http://scsbuster.nypl.org/refile)

SCSBuster creates "updates" and "transfers" in the sierra-updates-for-scsb SQS in exactly the same way that [SyncItemMetadataService](https://github.com/NYPL/sync-item-metadata-to-scsb-service/) does. (One small exception: updates & transfers created by the [SyncItemMetadataToSCSBListener](https://github.com/NYPL/sync-item-metadata-to-scsb-listener) include "source": "bib-item-store-update" to differentiate them from manual updates.) In the future we'd like SCSSBuster to use [SyncItemMetadataService](https://github.com/NYPL/sync-item-metadata-to-scsb-service/) for writing to SQS.

Note that "refile" requests made through SCSBuster do not generate Sierra-Updates-For-SCSB jobs. Refile requests are made entirely within our own infrastructure. A refile request is made by posting to our platform api at `recap/refile-requests`. (See [Appendix D: Refile Requests](#appendix-d-refile-requests).) The [RefileRequestService](https://github.com/NYPL/refile-request-service) [makes a SIP2 "checkin" call](https://github.com/NYPL/refile-request-service/blob/2f84aa0bc52351a6651a47a441014af6297e4367/src/Controller/RefileRequestController.php#L106-L110) against our ILS. This is done at different times in various workflows, often to clear "IN TRANSFER" or other unavailable statuses.

## Processing Sierra-Updates-For-SCSB Jobs

[SCSBItemUpdater](https://github.com/NYPL-discovery/scsb_item_updater) has two running workers: one consumes SQS and populates a secondary Redis queue. The other consumes that Redis queue.

The app [consumes SQS messages](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/dequeue_from_sqs.rb#L19-L24) and determines whether to hold them in the queue or process them. The app will process them if:
1. "old enough": the SQS message has [reached a certain age](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/sqs_message_handler.rb#L52) (this artificial delay accommodates manual update jobs by giving recent data updates time to propagate to the Bib/Item stores)
2. "process immediately": the SQS message [appears to have been generated by a Item/Bib store update (as opposed to a manual request via SCSBuster), so no delay is necessary](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/sqs_message_handler.rb#L46).

Whether because the message is old enough or flagged to be processed immediately, the job is next placed Redis based queue (interacted with via [Resque](https://github.com/resque/resque))

A dedicated worker [consumes](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/jobs/process_resque_message.rb#L10) messages from the Redis queue. After removing any barcode updates that appear to be unnecessary ([a mechanism best described here](https://github.com/NYPL-discovery/scsb_item_updater/blob/master/lib/jobs/process_resque_message.rb#L31-L67)), the worker [handles](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L11) the job as either an "update" or "transfer" based on "action".

### Processing Sierra-Updates-For-SCSB "Update" Jobs

When processing an "update", these things happen:

 * [Generates a hash](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L77) mapping barcodes to json "result" documents obtained via the SCSB API (See [Appendix A: SCSB API Search](#appendix-a-scsb-api-search))
 * [Creates a hash](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L84) relating barcodes to SCSB-XML representations (using barcode and customerCode queried above, fetches SCSBXML from `api/v0.1/recap/nypl-bibs`) (See [Appendix B: Generating SCSB-XML](#appendix-b-generating-scsb-xml))
 * [Submits the SCSBXML to SCSB](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L91) (See [Appendix C: Submitting SCSB-XML](#appendix-c-submitting-scsb-xml))
 * [Refiles all barcodes that *succeeded* above](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L96) via our own `api/v0.1/reap/refile-requests` endpoint (which calls "checkin" via SIP2) to ensure item status is available. (See [Appendix D: Refile Requests](#appendix-d-refile-requests))

The accumulated errors generated via each of those processes is emailed to the "user_email" attached to the job.

Jobs popped off the Redis queue are not re-queued under any circumstances; Failures are only noted by email.

### Processing Sierra-Updates-For-SCSB "Transfer" Jobs

When processing an "transfer", these things happen:

 * [Generates a hash](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L22) mapping barcodes to json "result" documents obtained via the SCSB API for the original bib ("source") in SCSB (See [Appendix A: SCSB API Search](#appendix-a-scsb-api-search))
 * **[Transfers the bib in SCSB](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L35)** by posting the source and destination bibids (See [Appendix E: SCSB Item Transfer](#appendix-e-scsb-item-transfer))
 * **[Removes any failed transfers from the array of barcodes to continue processing](https://github.com/NYPL-discovery/scsb_item_updater/blob/master/lib/resque_message_handler.rb#L39)**
 * [Creates a hash](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L44) relating barcodes to SCSB-XML representations (using barcode and customerCode queried above, fetches SCSBXML from `api/v0.1/recap/nypl-bibs`) (See [Appendix B: Generating SCSB-XML](#appendix-b-generating-scsb-xml))
 * [Submits the SCSBXML to SCSB](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L50) (See [Appendix C: Submitting SCSB-XML](#appendix-c-submitting-scsb-xml))
 * [Refiles all barcodes that *succeeded* above](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L53-L55) via our own `api/v0.1/reap/refile-requests` endpoint (which calls "checkin" via SIP2) to ensure item status is available. (See [Appendix D: Refile Requests](#appendix-d-refile-requests))

The notable difference between "transfer" and "update" is that we call [SCSB's "transfer" endpoint](https://scsb.recaplib.org:9093/swagger-ui.html#!/shared-collection-rest-controller/transferHoldingsAndItems) before submitting metadata.

### Errors

Errors can be thrown at several points in both "update" and "transfer" jobs. Errors are grouped by barcode and used to populate an email that is sent to the "user_email" associated with the request (in original SQS entry).

## Troubleshooting

### Incomplete records in SCSB

Sometimes Heide will note that certain records persist in the SCSB Incompletes report.

Often, you'll be handed the problematic barcodes. To get the list of problematic barcodes for yourself, you can use the SCSB UI to generate an Incompletes report. The SCSB Incompletes report can be obtained by logging into [SCSB UI](scsb.recaplib.org/) and navigating to Reports > Incomplete Records. Select "Show By" "NYPL" and click "Generate Report". Review the records shown or click "Export Records" to download a CSV.

The process of determining why a barcode persists as an Incomplete is:

**Before anything, check that the pollers are running and caught up**

In the code examples that follow, I use the [nypl-data-api-client](https://www.npmjs.com/package/@nypl/nypl-data-api-client) cli.

1. Check for item in ItemService:
  * Search ItemService by barcode (e.g. `node bin/nypl-data-api.js get items?barcode=33433122229572`)

2.A If item is not in ItemService, check Sierra:
  * Use Sierra desktop client to search for the item by barcode (Function "Catalog" > select "b Barcode" > enter barcode)

2.A.i If the item can be found in Sierra, see if item can be found by id in ItemService :
 * Examine id in Sierra (next to "Record", you'll see a number like 'i156163123'
 * Convert the "i-number" into an item id by removing the "i" prefix and dropping the final check digit (e.g. 'i156163123' becomes '15616312')
 * Now query the ItemService for the item by id: `node bin/nypl-data-api.js get items/sierra-nypl/15616312`

2.A.i.a If the item was not found in the ItemService by id, investigate a poller/retriever issue:
 * Navigate to the [CloudWatch logs for the retriever](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/SierraItemRetrieverRequest-production)
 * Enter the item id into the search (e.g. 37526855)
 * Optionally, restrict your search to the date range when you expect the retriever should have retrieved the item (e.g. if Sierra shows the item as having been last updated in the past few days, restrict your CloudWatch search to "1w" to make sure you completely cover the times when the retriever would have fetched the item)
 * If no issue was found, 

2.B If item is in ItemService:
  * If record appears, verify that the scsb-xml can be generated using the SCSBOngoingAccessions endpoint (e.g. 


## Appendix A: SCSB API Search

The query to find an item in SCSB looks like this:

```
curl -X POST --header 'Content-Type: application/json' --header 'Accept: */*' --header 'api_key: [APIKEY]' -d '{
  "deleted": false,
  "fieldValue": "33433121160935",
  "fieldName": "Barcode",
  "owningInstitutions": [
    "NYPL"
  ]
}' 'https://scsb.recaplib.org:9093/searchService/search'
```

A successful response resembles:
```
{
    "searchResultRows": [
        {
            "bibId": 5937051,
            "title": "Media Originals - SCL",
            "author": "   ",
            "publisher": null,
            "publisherDate": null,
            "owningInstitution": "NYPL",
            "customerCode": "NS",
            "collectionGroupDesignation": "Private",
            "useRestriction": "In Library Use",
            "barcode": "33433121160935",
            "summaryHoldings": "",
            "availability": "Available",
            "leaderMaterialType": "Monograph",
            "selected": false,
            "showItems": false,
            "selectAllItems": false,
            "searchItemResultRows": [],
            "itemId": 15458561,
            "owningInstitutionBibId": ".b207774110",
            "owningInstitutionHoldingsId": "e9f19f08-1227-4610-962d-76cadc2a52b2",
            "owningInstitutionItemId": ".i369234066",
            "requestPosition": null,
            "patronBarcode": null,
            "requestingInstitution": null,
            "deliveryLocation": null,
            "requestType": null,
            "requestNotes": null
        }
    ],
    "totalPageCount": 1,
    "totalBibRecordsCount": "1",
    "totalItemRecordsCount": "1",
    "totalRecordsCount": "1",
    "showTotalCount": false,
    "errorMessage": null
}
```

If a SCSB API query failed to identify an item by barcode (i.e. response includes `"searchResultRows": []`), we often follow up by searching "Incomplete" records as follows:

```
curl -X POST --header 'Content-Type: application/json' --header 'Accept: */*' --header 'api_key: [APIKEY]' -d '{
  "deleted": false,
  "fieldValue": "33433121160935",
  "fieldName": "Barcode",
  "owningInstitutions": [
    "NYPL"
  ],
  "collectionGroupDesignations": ["NA"],
  "catalogingStatus": "Incomplete"
' 'https://scsb.recaplib.org:9093/searchService/search'
```

"Incomplete" responses resemble standard query responses.

## Appendix B: Generating SCSB-XML

We maintain an endpoint for generating "SCSB XML", accessible at Platform API endpoint `recap/nypl-bibs`.

To generate SCSB XML for a given item, one needs to first look up the relevant `customerCode` (a location code understood by the SCSB API). The correct customerCode is found by [querying the SCSB API](#appendix-a-scsb-api-search)

The request resembles:

```
curl -X GET "https://platform.nypl.org/api/v0.1/recap/nypl-bibs?customerCode=NC&barcode=33433121134914&includeFullBibTree=false" -H  "accept: text/xml" -H  "authorization: Bearer [BEARER TOKEN]"
```

The response may resemble:
```
<?xml version="1.0" ?>
  <bibRecords>
    <bibRecord>
      <bib>
        <owningInstitutionId>NYPL</owningInstitutionId>
        <owningInstitutionBibId>.b207774110</owningInstitutionBibId>
        <content>
          <collection xmlns="http://www.loc.gov/MARC21/slim">
            <record>
              <datafield ind1="8" ind2=" " tag="952">
                <subfield code="h">SCL 23177</subfield>
              </datafield>
              <datafield ind1="1" ind2="0" tag="245">
                <subfield code="a">Media Originals - SCL</subfield>
              </datafield>
              <datafield ind1=" " ind2=" " tag="901">
                <subfield code="b">SFP</subfield>
                <subfield code="a">SFP</subfield>
              </datafield>
              <datafield ind1="0" ind2="0" tag="907">
                <subfield code="a">.b207774110</subfield>
              </datafield>
              <leader>00000nam  2200000 a 4500</leader>
            </record>
          </collection>
        </content>
      </bib>
      <holdings>
        <holding>
          <owningInstitutionHoldingsId/>
          <content>
            <collection xmlns="http://www.loc.gov/MARC21/slim">
              <record>
                <datafield ind1="8" ind2=" " tag="852">
                  <subfield code="b">rccb9</subfield>
                  <subfield code="h">SCL 23177</subfield>
                </datafield>
                <datafield ind1=" " ind2=" " tag="866">
                  <subfield code="a">box 4133</subfield>
                </datafield>
              </record>
            </collection>
          </content>
          <items>
            <content>
              <collection xmlns="http://www.loc.gov/MARC21/slim">
                <record>
                  <datafield ind1=" " ind2=" " tag="876">
                    <subfield code="p">33433121134914</subfield>
                    <subfield code="h">In Library Use</subfield>
                    <subfield code="a">.i369264976</subfield>
                    <subfield code="j">Available</subfield>
                    <subfield code="t">1</subfield>
                    <subfield code="3">box 4133</subfield>
                  </datafield>
                  <datafield ind1=" " ind2=" " tag="900">
                    <subfield code="a">Private</subfield>
                    <subfield code="b">NC</subfield>
                  </datafield>
                </record>
              </collection>
            </content>
          </items>
        </holding>
      </holdings>
    </bibRecord>
  </bibRecords>
```

## Appendix C: Submitting SCSB-XML

Having [generated SCSB-XML](#appendix-b-generating-scsb-xml), the call to submit that metadata to SCSB resembles:

```
curl -X POST --header 'Content-Type: application/json' --header 'Accept: */*' --header 'api_key: [APIKEY]' -d '
<bibRecords><bibRecord><bib><owningInstitutionId>NYPL</owningInstitutionId><owningInstitutionBibId>.b160883088</owningInstitutionBibId><content><collection xmlns="http://www.loc.gov/MARC21/slim"><record><controlfield tag="001">57045483</controlfield><controlfield tag="003">OCoLC</controlfield><controlfield tag="005">20050701140306.6</controlfield><controlfield tag="008">041124s2005    jm     j      000 f eng dcamIa </controlfield><datafield ind1="1" ind2=" " tag="100"><subfield code="a">Chase, Barbara A.</subfield></datafield><datafield ind1="2" ind2=" " tag="791"><subfield code="a">Schomburg Children's Collection.</subfield></datafield><datafield ind1="8" ind2=" " tag="952"><subfield code="h">Sc D 05-1115</subfield></datafield><datafield ind1=" " ind2="0" tag="650"><subfield code="a">AIDS (Disease)</subfield><subfield code="v">Fiction.</subfield></datafield><datafield ind1=" " ind2="0" tag="650"><subfield code="a">HIV infections</subfield><subfield code="v">Fiction.</subfield></datafield><datafield ind1=" " ind2="0" tag="651"><subfield code="a">Barbados</subfield><subfield code="v">Fiction.</subfield></datafield><datafield ind1=" " ind2=" " tag="690"><subfield code="a">Black author.</subfield></datafield><datafield ind1=" " ind2="7" tag="655"><subfield code="a">Didactic fiction.</subfield><subfield code="2">lcgft</subfield></datafield><datafield ind1=" " ind2=" " tag="020"><subfield code="a">9766371792</subfield></datafield><datafield ind1=" " ind2=" " tag="260"><subfield code="a">Kingston, Jamaica :</subfield><subfield code="b">Ian Randle,</subfield><subfield code="c">2005.</subfield></datafield><datafield ind1="8" ind2=" " tag="952"><subfield code="h">Sc D 05-1115</subfield></datafield><datafield ind1=" " ind2=" " tag="300"><subfield code="a">121 p. ;</subfield><subfield code="c">22 cm.</subfield></datafield><datafield ind1="1" ind2="4" tag="245"><subfield code="a">The silent killer /</subfield><subfield code="c">Barbara Chase.</subfield></datafield><datafield ind1=" " ind2=" " tag="959"><subfield code="a">.b77879879</subfield><subfield code="b">07-20-07</subfield><subfield code="c">05-19-05</subfield></datafield><datafield ind1=" " ind2=" " tag="040"><subfield code="a">BWI</subfield><subfield code="c">BWI</subfield><subfield code="d">OCLCQ</subfield><subfield code="d">NYP</subfield><subfield code="d">UtOrBLW</subfield></datafield><datafield ind1=" " ind2=" " tag="043"><subfield code="a">nwbb---</subfield></datafield><datafield ind1=" " ind2=" " tag="049"><subfield code="a">NYPP</subfield></datafield><datafield ind1=" " ind2=" " tag="901"><subfield code="b">sg</subfield><subfield code="c">SCR/MRW</subfield></datafield><datafield ind1=" " ind2=" " tag="946"><subfield code="a">m</subfield></datafield><datafield ind1=" " ind2=" " tag="997"><subfield code="a">sg</subfield><subfield code="b">07-05-05</subfield><subfield code="c">m</subfield><subfield code="d">a</subfield><subfield code="e">-</subfield><subfield code="f">eng</subfield><subfield code="g">jm </subfield><subfield code="h">4</subfield></datafield><datafield ind1="0" ind2="0" tag="907"><subfield code="a">.b160883088</subfield></datafield><datafield ind1=" " ind2=" " tag="035"><subfield code="a">(OCoLC)57045483</subfield></datafield><leader>00000cam  2200313Ia 4500</leader></record></collection></content></bib><holdings><holding><owningInstitutionHoldingsId/><content><collection xmlns="http://www.loc.gov/MARC21/slim"><record><datafield ind1="8" ind2=" " tag="852"><subfield code="b">rcma2</subfield><subfield code="h">Sc D 05-1115</subfield></datafield><datafield ind1=" " ind2=" " tag="866"><subfield code="a"/></datafield></record></collection></content><items><content><collection xmlns="http://www.loc.gov/MARC21/slim"><record><datafield ind1=" " ind2=" " tag="876"><subfield code="p">33433068445950</subfield><subfield code="h"/><subfield code="a">d30279</subfield><subfield code="j">Available</subfield><subfield code="t">1</subfield></datafield><datafield ind1=" " ind2=" " tag="900"><subfield code="a">Shared</subfield><subfield code="b">NA</subfield></datafield></record></collection></content></items></holding></holdings></bibRecord></bibRecords>
' 'https://scsb.recaplib.org:9093/sharedCollection/submitCollection?institution=nypl&isCGDProtected=true'
```

A successful response for above resembles:

```
[
    {
        "itemBarcode": "33433068445950",
        "message": "Success record"
    }
]
```

## Appendix D: Refile Requests

A request to refile an item by barcode resembles:

```
curl -X POST "https://platform.nypl.org/api/v0.1/recap/refile-requests" -H  "accept: application/json" -H  "authorization: Bearer [BEARER TOKEN]" -H  "Content-Type: application/json" -d "{  \"itemBarcode\": \"33433068445950\"}"
```

A success response resembles:

```
{
  "data": {
    "id": 6563,
    "jobId": "68965cdd902d20ed2",
    "success": true,
    "createdDate": "2019-05-16T12:30:37-04:00",
    "updatedDate": "2019-05-16T12:30:39-04:00",
    "itemBarcode": "33433068445950",
    "afMessage": null,
    "sip2Response": "{\"fixed\":{\"Ok\":\"1\",\"Resensitize\":\"Y\",\"Magnetic\":\"N\",\"Alert\":\"N\",\"TransactionDate\":\"201905160000123039\"},\"variable\":{\"Raw\":[\"AOnypl \",\"AB33433068445950\",\"AQrcma2\",\"AJThe silent killer \\/ Barbara Chase.\",\"CK000\",\"AF\",\"CSSc D 05-1115 \",\"CRrcma2\",\"CT     \",\"CV\",\"CY\",\"DA\",\"AY0\"],\"AO\":[\"nypl \"],\"AB\":[\"33433068445950\"],\"AQ\":[\"rcma2\"],\"AJ\":[\"The silent killer \\/ Barbara Chase.\"],\"CK\":[\"000\"],\"CS\":[\"Sc D 05-1115 \"],\"CR\":[\"rcma2\"],\"AY\":[\"0\"],\"AZ\":[\"D4F0\\r\"]}}"
  },
  "count": 1,
  "totalCount": 0,
  "statusCode": 200,
  "debugInfo": []
}
```

Failures are indicated by HTTP response codes >= 400 and additional information in returned "message" (i.e. `JSON.parse(response.body)['message']).

## Appendix E: SCSB Item Transfer

A request to transfer an item from one bib to another in SCSB resembles:

```
curl -X POST --header 'Content-Type: application/json' --header 'Accept: */*' --header 'api_key: [API_KEY]' -d '{
 "itemTransfers": [
   {
     "source": {
       "owningInstitutionBibId": ".b207774110",
       "owningInstitutionHoldingsId": "9fe80879-dc00-4ea4-8ea3-978191f6406a",
       "owningInstitutionItemId": ".i369264976"
     },
     "destination": {
       "owningInstitutionBibId": ".b207774110newbib",
       "owningInstitutionHoldingsId": ".b207774110newbib-4dc4fbd6-2dd3-4757-9b17-1ff05e7f3773",
       "owningInstitutionItemId": ".i369264976"
     }
   }
 ],
 "institution": "NYPL"
}' 'https://scsb.recaplib.org:9093/sharedCollection/transferHoldingsAndItems'
```

A success response for above minimally includes the following:
```
{
  "message": "Success"
}
```

A failed response may have HTTP response code 200, but resemble:

```
{
    "message": "Failed",
    "holdingTransferResponses": [],
    "itemTransferResponses": [
        {
            "message": "Source holdings is not under source bib",
            "itemTransferRequest": {
                "source": {
                    "owningInstitutionBibId": ".b207774110",
                    "owningInstitutionHoldingsId": "9fe80879-dc00-4ea4-8ea3-978191f6406a",
                    "owningInstitutionItemId": ".i369264976"
                },
                "destination": {
                    "owningInstitutionBibId": ".b207774110newbib",
                    "owningInstitutionHoldingsId": ".b207774110newbib-4dc4fbd6-2dd3-4757-9b17-1ff05e7f3773",
                    "owningInstitutionItemId": ".i369264976"
                }
            }
        }
    ]
}
```

