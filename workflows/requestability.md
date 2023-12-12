
# Overview
There are two dependent values used in requestability determination. Requestability, which encompasses physical, EDD, and special requestability, relies on a non-empty `item.deliveryLocation` value. Generally, for an item to be physical requestable, it has to have at least one delivery location. The exception to this is partner items missing customer codes, see here for more info on that. `eddRequestable` is determined alongside delivery locations, though it is a boolean value. This grouping is due to needing delivery locations (including `eddRequestable`) to be served by a specific endpoint, while requestability is needed for the `discovery/resources` endpoint. There is talk of refactoring this coupled area of code.
## DELIVERABILITY
Universal disqualifiers: no holding location (for NYPL owned items), no barcode (these cases are both logged at debug level in various places).
## NYPL core
#### URLs
[M2](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/m2CustomerCodes.csv)

[ReCAP](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/recapCustomerCodes.csv)

[Sierra Holding Location](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/locations.csv)

#### Flow
The process to find delivery values is as follows:
1. Reference the appropriate csv in nypl-core

    a. Note that for all NYPL-owned items, the flow begins in the Sierra Holding Location csv, to check for deliverableToResolution. That value will be either M2, ReCAP or blank (defaulting to that csv).
2. Find the relevant customer code in the `skos:notation` column (should be the first one)
3. For NYPL owned items, check the requestable column
4. Find are delivery locations (represented as customer codes or Sierra holding locations) listed under deliverableTo column
#### Physical
Disqualifiers: requestable: false, no deliverable to values
#### Onsite
1. check for holding location requestable in sierra locations csv. If it is false, item is NOT requestable
2. If location is requestable, check for `deliverableToResolution`

    a. M1 (or no specified resolution) => return delivery locations from `sierra locations.csv`

    b. M2 => return delivery locations from `m2-customer-codes.csv`
#### RECAP
* For nypl items with requestable holding locations or all partner records, return sierra delivery locations specified in nypl-core's `recap-customer-codes.csv`
* If the item is NYPL-owned with an unrequestable holding location, phys and edd requestability is false.

### EDD
#### Onsite
* If item's `status`, `accessMesssage`, `catalogItemType`, and `holdingLocation` match the values found in `discovery-api/data/onsite-edd-criteria.json` (snapshot found in appendix), the item is EDD requestable.
#### Recap
* if item is NYPL-owned with unrequestable holding location, edd requestability is false.
* for partner records or nypl items with requestable holding locations, return `eddRequestable` specified in nypl-core's `recap-customer-codes.csv`
* missing recap customer code items default to edd requestable = true.

    * We give these default true edd equestable values because partner items that we index are necessarily requestable. Before making a hold request, there is a SCSB query made to get the updated status and customer code. The hold request page is then rendered using up to date SCSB data.

# REQUESTABILITY
All of these values are true/false based on the criteria specified below
## eddRequestable
* as returned by deliverability resolver function (which function is determined by requestability resolver)
## physRequestable
* presence of any delivery locations
* physRequesability is logged at debug level with criteria
## specRequestable
* presence of `aeonUrl`

# Appendix
Onsite edd criteria snapshot:
As of October 24, 2023:
```
{
  "status": [
	"a"
  ],
  "accessMessage": [
	"-","1","u"
  ],
  "catalogItemType": [
	"2","3","4","5","32","33","42","43","52","53","54","55","60","61","62","63","64","65"
  ],
  "holdingLocation": [
	"mab82","mab92","maf","maf82","maf92","maff1","maff3","mag","mag82","mag92","magg1","magg2","magg3","magh1","mai","mai82","mai92","maii1","maii2","maii3","maj92","mak","mak82","makk3","mal","mal72","mal82","mal92","mall1","malm2","malv2","map","map82","map92","mapp1","mapp2","mapp3","mas62","mas82","mas92","pad22","pad32","pah","pah32","pam","pam32","par","pat","pat22","pat32","scf","scff1","scff2","scff3"
  ]
}
```
