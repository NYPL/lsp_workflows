# Add SCSB Location

This document describes how to make recently added Sierra locations usable as delivery locations in SCC.

## Overview

There are two different kinds of locations:
 * locations (aka Sierra locations): These are location codes found in Sierra (including locations not involved in ReCAP).
 * ReCAP locations (aka customer codes): ReCAP minted new unique identifiers called "customer codes" for every ReCAP partner location it ever sees. They all thus map to either one of our Sierra locations or a partner location.

When a NYPL Sierra location has an equivalent ReCAP location, that link is made in the Sierra location as `nypl:recapCustomerCode`.

It may be useful to preface this with: within the domain of "locations" (and among ReCAP locations) there are two disjoint categories of location that emerge from how they are used:
 * Holding locations: Locations that are referenced directly from an item indicate the location where the physical item is stored. The holding location links to zero or more delivery locations.
 * Delivery locations: Locations to which one may request that an item be sent. Delivery locations are never also holding locations. The set of delivery locations for an item is the set of delivery locations referenced by the item's holding location.

## To add a location, first gather some information

For each location you'll add, you should gather info for the new location and ReCAP location (customer code).

Note the following is a targetted distillation of information in [Discovery Properties](https://docs.google.com/spreadsheets/d/1qTjXqCO4eusaxr6MGpb7ns4u6k8hmg0s6LzJWvHhmHI/edit#gid=493047939).

### Location

* **Code (skos:notation)**: Three-four character code uniquely identifying the location in Sierra (e.g. 'mal', 'sce')
* **Label (skos:prefLabel)**: Full name of location shown to staff & patrons in SCC (e.g. "Schwarzman Building - Main Reading Room 315", "Schomburg Center - Photographs & Prints")
* **Sierra label (skos:altLabel)**: A slightly shorter label used by Sierra (e.g. "SASB - Service Desk Rm 315", "Schomburg Prints & Photographs")
* **Sublocation of (dcterms:isPartOf)**: Typically two-character code identifying parent location (e.g. 'ma', 'sc') 
* **Delivery location type (nypl:deliveryLocationType)**: Must be 'Branch', 'Research', or 'Scholar' to indicate the class of patron that may have materials delivered to the location. Branch locations are 'Branch'. Everything else is 'Research' unless it's a designated 'Scholar' room.
* **Location Slug (nypl:locationsSlug)**: The "slug" identifying the record in the Locations API most relevant to this location. I believe this is largely a formality, not used. (e.g. 'general-research-division', 'schomburg')
* **Owner (nypl:owner)**: The NYPL center, division, branch, or unit responsible for the location (links into [NYPL-Core Organizations](https://github.com/NYPL/nypl-core/blob/master/vocabularies/json-ld/organizations.json)). (e.g. 'http://data.nypl.org/orgs/1000', 'http://data.nypl.org/orgs/1118')
* **Requestable (nypl:requestable)**: Boolean indicating whether items assigned this location can be requested *in SCC*. Note that this is meaningless (and thus `false`) for delivery locations because items are never assigned home locations that are also delivery locations. Requestable will be `true` only for those locations that are used as the "home" location of items in ReCAP that may be requested (e.g. 'rc', 'rc2cf', 'rc2cf')
* **Collection type (nypl:collectionType)**: The library collection, Research or Branch, that a location's items belong to. Used by the SCC data pipeline as one of a few checks used to determine if an item is "research" or "branch". A location might contain items from both collections.
* **Deliverable to**: Locations where a holding location's materials may be served. Only relevant for locations that are holding locations.
* **ReCAP customer code**: This uniquely identifies the location in ReCAP.
* **Allow sierra hold (nypl:allowSierraHold)**: Boolean that should be `true` for any holding location whose items are requestable via native Sierra interfaces. Will be `false` (or unset) for ReCAP locations. (I believe this property is maintained as a formality; The mechanism for showing/suppressing locations lies elsewhere. It appears to often be wrong, e.g. many Scholar rooms delivery locations have it marked as `true`)

### ReCAP Customer Code

* **ReCAP customer code**: This uniquely identifies the location in ReCAP. All customer codes map to a single NYPL/partner location. Customer codes tend to be minted after a new Sierra location is created/proposed. (e.g. 'NH', 'SP')
* **ReCAP Label**: Label used by ReCAP. Mostly for documentation purpose; Not shown in any interface. (e.g. "SASB Rose Main Reading Room", "Schomburg Prints & Photographs")
* **ReCAP locations that may deliver to this location**: The set of ReCAP locations (customer codes) whose items may be delivered to this location.
* **ReCAP locations that items at this location may deliver to**: Less commonly, if the location added is assigned as the `customerCode` (i.e. home location) of an item, to what locations may that item be delivered?

### M2 Customer Code

* **code**: Unique identifier
* **label**: Label
* **deliverableTo**: The set of M2 customer codes that items in this customer code can be delivered to
* **requestable**: Whether or not items in this code may be requested
* **Assocated Sierra location**: Sierra location code equivalent

## Add entries to NYPL-Core

Having collected the above information, add the relevant data to [locations.csv](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/locations.csv), [recapCustomerCodes.csv](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/recapCustomerCodes.csv), and [m2CustomerCodes.csv](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/m2CustomerCodes.csv).

Be sure to include links between entries:
 - If adding a new delivery location, be sure the appropriate holding locations include the new location in relevant `deliverableTo` properties.
 - If adding a new holding location, be sure the deliverableTo includes appropriate entries (usually modelled on a similar location)

Review previous similar additions as a reference:
 - [Addition of mal23 scholar room with associated updates to M2 and ReCAP customer codes](https://github.com/NYPL/nypl-core/compare/v2.19...v2.x-mal23-3)

Follow instructions on [nypl-core](https://github.com/NYPL/nypl-core) for testing, reviewing, tagging, and publishing your changes.

### To test changes to NYPL-Core

To test a location change ahead of it going live:

1. [Make the change in NYPL-Core as a pre-release](https://github.com/NYPL/nypl-core#general-workflow-for-changes)
1. Change HoldRequestConsumer-qa `NYPL_CORE_VERSION` to pre-release version number (e.g. `v1.29a`)
1. [Publish your changes to the QA S3 bucket](https://github.com/NYPL/nypl-core-objects#pushing-to-s3) (e.g. `NYPL_CORE_VERSION=v1.29a npm run deploy-qa`).
1. Make sure the HoldRequestConsumer-qa has `NYPL_CORE_VERSION` set to your pre-release version number
1. Make sure the HoldRequestResultConsumer-qa has `API_RECAP_LOCATION_URL` and `API_SIERRA_LOCATION_URL` configured for 'qa' S3 (note this app *encrypts* these config values..)
   * This component uses the customerCode and sierra location mapping files in S3 to derive the proper location labels for `deliveryLocation` and `pickupLocation`, which are set exclusively for requests originating from the SCSB UI and SCC, respectively. The labels are used in an email sent to the patron.
1. Make sure the RecapHoldRequestConsumer-qa is configured with a 'qa' S3 `LOCATIONS_URL`
   * This component uses the sierra locations mapping to translate customer codes into sierra locations
1. [Add the location(s) to the discovery-front-end](https://github.com/NYPL-discovery/discovery-front-end/blob/0e96af0e2d944657805d17c06ec3ff2a13a913ee/README.md#adding-locations)
1. Update the discovery-api-qa Elasticbeanstalk app to `NYPL_CORE_VERSION` to the pre-release version number

Now you can test a few different angles:
1. Confirm delivery location changes by hitting the delivery locations endpoint via [NYPL data api client cli](https://github.com/NYPL-discovery/node-nypl-data-api-client)
   - e.g. to test a scholar: `node bin/nypl-data-api.js get request/deliveryLocationsByBarcode?barcodes[]=33433061301572\&patronId=5427701`
1. Confirm delivery location changes via SCC
   - e.g. visit https://qa-www.nypl.org/research/collections/shared-collection-catalog/hold/request/b10000020-i13783786 with [different patrons](https://docs.google.com/spreadsheets/d/1S693bKROtRfU9ow4UkLGxTVScYfBvJqoV6yHRKG7bmk/edit#gid=1625093641)

### To push NYPL-Core changes to Production

1. Promote your pre-release to a release per [NYPL-Core instructions](https://github.com/NYPL/nypl-core#for-production)
1. Make extra sure that the new NYPL-Core version tag resolves and reflects your changes by checking `https://github.com/NYPL/nypl-core/tree/[NYPL_CORE_VERSION]/vocabularies`
1. [Publish your changes to the Production S3 bucket](https://github.com/NYPL/nypl-core-objects#pushing-to-s3) (e.g. `npm run deploy-production`).
1. Ensure the locations have been [added to the discovery-front-end](https://github.com/NYPL-discovery/discovery-front-end/blob/0e96af0e2d944657805d17c06ec3ff2a13a913ee/README.md#adding-locations) in Production
1. Make sure the discovery-api-production Elasticbeanstalk app has latest `NYPL_CORE_VERSION` (or "master"). Restart app server if you make any change (as simply changing the ENV var [does not cause app code to reevaluate the variable](https://github.com/NYPL-discovery/discovery-api/issues/136)).

Note that no change to `HoldRequestResultConsumer-production` is necessary for Production deployment because it [draws on the production S3 bucket for every lookup](https://github.com/NYPL/hold-request-result-consumer/blob/master/src/OAuthClient/LocationClient.php#L16). Similarly, no change is necessary for `RecapHoldRequestConsumer-production because it also [downloads the production S3 mapping for every lookup](https://github.com/NYPL/recap-hold-request-consumer/blob/bb8b00c46552c250b6c1b2bc7af245b4d0664978/models/location.rb#L9).
