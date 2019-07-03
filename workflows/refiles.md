# Refiles

The stated purpose of refile is to "reset" item status. Specifically, it handles the following scenario:

 - *In Transit*: (i.e. `status.code == "t"`) Item status is cleared
 - *Checked out*: (i.e. `status.code == "-" && status.duedate != ""`) Item status is cleared
 - *Available*: (i.e. `status.code == "-" && status.duedate == ""`) Item status is unchanged (no-op)

The following statuses are not handled well:

 - *On hold*: An item with any status can have an active hold. When refiled, an item with an active hold will have its status changed to "!", "ON HOLDSHELF".
 
An item with an active item-level hold is currently not differentiated from one with no item-level holds. An item with an item-level hold will - when refiled - be converted to "ON HOLDSHELF"

## The Refile Implementation

We're using SIP2 Checkin for refile. This specific call has the effect of clearing the status in many cases but does something a little different for cases where there's an active item level hold. When there's an item level hold, Checkin changes the status to "ON HOLDSHELF", presumably because the call is generally triggered by a human with a barcode scanner physically handling the book. An item with an active hold that has just been scanned generally is bound for the holdshelf. It's a convenience.

## Issues

### Rogue Item-Level Holds

Holds placed outside SCC or SCSB UI create trouble because SCC and SCSB are the authority for holds on items in ReCAP. For example, if a patron manages to circumvent our JS overrides in Classic to create an item-level hold on an item in ReCAP:

 - Sierra will update the `updatedDate` for the item record (nothing else)
 - ItemPoller will pick up the change, ultimately sending the item through the `Item` stream
 - `SyncItemMetadataToScsbListener` will pick up the "change" and - because it's a ReCAP item, post the item to the `SyncItemMetadataToScsbService`
 - `SyncItemMetadataToScsbService` will pick up the update and post it to the scsb-item-updates SQS
 - `SCSBItemUpdater` will pick up the update and attempt to sync metadata including:
   - Post latest SCSBXml to SCSB API (although it will be unchanged)
   - Post the barcode to our `RefileRequestService`
 - `RefileRequestService` will call SIP2 Checkin, causing item status to change to 'ON HOLDSHELF' (and email patron)
 
In effect, the patron will receive a notification that their item is waiting for them roughly 45s after placing a hold request. Worse, SCSB will have no knowledge of the hold request; the item will remain 'Available'.

### Soft Cancelled Holds

Items returned to ReCAP must have active holds cancelled. Sometimes the following happens:

 - A patron places a hold request through SCC or via staff (through SCSB UI)
 - SCSB sends the item to the pickup location
 - The item is returned to ReCAP because the patron does not want it (or time expires) *without* cancelling hold
 - ReCAP staff retrieve the item, re-shelve it, and call our Refile endpoint, causing it to flip to "ON HOLDSHELF"
