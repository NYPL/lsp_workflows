# SCSB Item Updates

A subset of items in NYPL's catalog are stored offsite at ReCAP and inventoried by a system called SCSB. For those items, SCSB is the authority for an item's location & status. SCSB also stores bibliographic data for those items. This document describes the process by which our ILS is kept in sync with SCSB for item status and data.

Metadata updates are propagated from our ILS to SCSB via both automatic and manual means. In both cases the actual update is managed by a component consuming a "sierra-updates-for-scsb" SQS. The following describes the two ways that SQS can be populated.

## Automatic creation of Sierra-Updates-For-SCSB Jobs

### Listen for updates on Item, Bib event streams to create sierra-update-for-scsb jobs

[SyncItemMetadataToSCSBListener](https://github.com/NYPL/sync-item-metadata-to-scsb-listener) listens on Bib & Item kinesis streams (representing all updates to bibs and items).

*For each item*, the component determines if it's an item stored in ReCAP [based on the item's location](https://github.com/NYPL/sync-item-metadata-to-scsb-listener/blob/0c7470aa39cd4c53313c3d70fa074f5688f4c34c/lib/item_handler.rb#L8). If the item is determined to be in ReCAP, [it determines whether the data should be processed as an "update" (modified metadata) or a "transfer" (changed bib ownership)](https://github.com/NYPL/sync-item-metadata-to-scsb-listener/blob/0c7470aa39cd4c53313c3d70fa074f5688f4c34c/lib/item_handler.rb#L54-L57). Having made that determination, it writes the resulting job to the [SyncItemMetadataToSCSBService](https://github.com/NYPL/sync-item-metadata-to-scsb-service/), e.g.:

```
{ "barcodes": [ "123456" ], "user_email": "[registered email to send errors to]@nypl.org", "action": "update", "source": "bib-item-store-update" }
```

Note the "source" property identifies this update job as originating from an organic update in the ItemService. (This is a helpful hint downstream when handling the update as it indicates the relevant data has already been persisted to the ItemService at the time the SQS update job was written.)

If the update is determined to be a "transfer" (i.e. item assigned a new bibid), it may look like this:

```
{ "barcodes": [ "123456" ], "user_email": "[registered email to send errors to]@nypl.org", "action": "transfer", "bib_record_number": "newbibnum", "source": "bib-item-store-update" }
```

*For each bib*, the component determines if it's a bib _potentially_ with items stored in ReCAP based on whether 1) its first item is research, or 2) it's a known mixed-bib (a bib with both research and branch items). In either case, the bib definitely *might* have items in ReCAP, so we proceed by submitting all related item barcodes to the [SyncItemMetadataToSCSBService](https://github.com/NYPL/sync-item-metadata-to-scsb-service/) as "update" jobs, e.g.:

```
{ "barcodes": [ "123456", "6789" ], "user_email": "[registered email to send errors to]@nypl.org", "action": "update" }
```

### Create Sierra-Updates-For-SCSB jobs

The [SyncItemMetadataService](https://github.com/NYPL/sync-item-metadata-to-scsb-service/) validates and writes incoming jobs to a "sierra-updates-for-scsb" SQS.

An acceptable incoming "update" job might look like this ("action" defaults to "update"):

```
{ "barcodes": [ "123456" ], "user_email": "staff-email@nypl.org" }
```

An acceptable incoming "transfer" job might look like this:

```
{ "barcodes": [ "123456" ], "user_email": "staff-email@nypl.org", "action": "transfer": "transfer", "bib_record_number": "newbibnum" }
```

## Manual creation of Sierra-Updates-For-SCSB Jobs

The other method for populating the sierra-updates-for-scsb SQS is [SCSBuster](https://github.com/NYPL/scsbuster).

### SCSBuster

SCSBuster allows:

 * *Updates*: One can [manually queue "update" SQS jobs](http://scsbuster.nypl.org/update_metadata) by barcode(s)
 * *Transfer*: One can [manually queue "transfer" SQS jobs](http://scsbuster.nypl.org/transfer_metadata) by barcode (and destination bibid)
 * *Refile*: One can [manually call "refile" and view a log of refile errors](http://scsbuster.nypl.org/refile)

SCSBuster creates "updates" and "transfers" in the sierra-updates-for-scsb SQS in exactly the same way that [SyncItemMetadataService](https://github.com/NYPL/sync-item-metadata-to-scsb-service/) does. (One small exception: updates & transfers created by the [SyncItemMetadataToSCSBListener](https://github.com/NYPL/sync-item-metadata-to-scsb-listener) include "source": "bib-item-store-update" to differentiate them from manual updates.) In the future we'd like SCSSBuster to use [SyncItemMetadataService](https://github.com/NYPL/sync-item-metadata-to-scsb-service/) for writing to SQS.

## Processing Sierra-Updates-For-SCSB Jobs

[SCSBItemUpdater](https://github.com/NYPL-discovery/scsb_item_updater) has two running workers: one consumes SQS and populates a secondary Redis queue. The other consumes that Redis queue.

The app [consuming SQS messages](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/dequeue_from_sqs.rb#L19-L24) and determines whether to hold them in the queue or process them. The app will process them if:
1. "old enough": the SQS message has [reached a certain age](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/sqs_message_handler.rb#L52) (this artificial delay accommodates manual update jobs by giving recent data updates time to propagate to the Bib/Item stores)
2. "process immediately": the SQS message [appears to have been generated by an organic Item/Bib store update, so no delay is necessary](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/sqs_message_handler.rb#L46).

Whether because the message is old enough or flagged to be processed immediately, the next stage is a Redis based queue interfaced by [Resque](https://github.com/resque/resque)

A dedicated worker [consumes](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/jobs/process_resque_message.rb#L10) messages from the Redis queue. After removing any barcode updates that appear to be unnecessary ([a mechanism best described here](https://github.com/NYPL-discovery/scsb_item_updater/blob/master/lib/jobs/process_resque_message.rb#L31-L67)), the worker [handles](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L11) the job as either an "update" or "transfer" based on "action".

*When processing an "update"*, these things happen:

 * [Generates a hash](https://github.com/NYPL-discovery/scsb_item_updater/blob/master/lib/resque_message_handler.rb#L77) mapping barcodes to json "result" documents obtained via the SCSB API
 * [Creates a hash](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L84) relating barcodes to SCSB-XML representations (using barcode and customerCode queried above, fetches SCSBXML from `api/v0.1/recap/nypl-bibs`)
 * [Submits the SCSBXML to SCSB](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L91)
 * [Refiles all barcodes that *succeeded* above](https://github.com/NYPL-discovery/scsb_item_updater/blob/0e26f566f29afc146510edaf5ceece2b5bcbe381/lib/resque_message_handler.rb#L96) via our own `api/v0.1/reap/refile-requests` endpoint (which calls "checkin" via SIP2) to ensure item status is available.

The accumulated errors generated via each of those processes is emailed to the "user_email" attached to the job.

Jobs popped off the Redis queue are not re-queued under any circumstances; Failures are only noted by email.
