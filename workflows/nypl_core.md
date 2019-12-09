# NYPL Core

NYPL Core is a set of interrelated vocabularies living at [http://github.com/NYPL/NYPL-Core](http://github.com/NYPL/NYPL-Core). It's the culimation of a great deal of modelling work collected in the ["Discovery properties" Google Sheet](https://docs.google.com/spreadsheets/d/1qTjXqCO4eusaxr6MGpb7ns4u6k8hmg0s6LzJWvHhmHI/edit#gid=493047939).

## Typical workflow

Edits to NYPL Core tend to work like this:

1. A request comes in asking for a location/ptype change
1. The change is [added to NYPL-Core as a PR with a pre-release tag](https://github.com/NYPL/nypl-core#for-qa)
1. The pre-release tag is used to preview the change in our QA stack (i.e. by setting `NYPL_CORE_VERSION` to the pre-release tag in effected components)
1. If the effected components rely on an S3 lookups, one may need to do a QA "deploy" of NYPL-Core Objects S3 assets (e.g. `NYPL_CORE_VERSION=v1.29a npm run deploy-qa`)
1. After QC & approval, the feature is merged and a new release tag is created.
1. Deploy NYPL Core Objects (i.e. to ensure S3 lookups are in sync with your changes)

The specific requirements depend on what part of NYPL Core is changing. Locations are most tricky and [are documented in the "Add SCSB Location" workflow](https://github.com/NYPL/lsp_workflows/blob/master/workflows/add_scsb_location.md#add-entries-to-nypl-core).

## Things that depend on NYPL-Core

All interactions noted below occur through [NYPL Core Objects](https://www.npmjs.com/package/@nypl/nypl-core-objects) unless otherwise noted. NYPL Core Objects is a simple wrapper, which 1) handles fetching raw assets from NYPL Core and 2) converts them into a hash optimized for the kinds of id lookups we tend to need to do.

### Discovery Front End

DiscoveryFrontEnd has a funny relationship with NYPL-Core. It does not use it directly but does maintain its own static hash of location data that must be in agreement with entries in NYPL Core. This is not an ideal situation. [Best described here](https://github.com/NYPL-discovery/discovery-front-end/blob/9a32fccd212fc644503ed0e516f59e254340f335/README.md#adding-locations)

### Discovery API

The Discovery API uses NYPL Core for two purposes:

**Delivery Locations By Barcode**

The Discovery API serves a delivery-locations-by-barcode endpoint for determining the delivery locations available to a patron for a specific item. It's used by the DiscoveryFrontEnd to display available delivery options.

For an overview of how the options are computed, [see this section of the workflow on SCSB Locations](https://github.com/NYPL/lsp_workflows/blob/18953c472cd9ad5f626040e7bbc7f1bc9fcd706e/workflows/add_scsb_location.md#a-note-on-the-holding-delivery-location-relationship)

1. The list of delivery locations is developed by examining the item's customer code (as returned by SCSB API) and using that as a key into the `by-recap-customer-code` NYPL-Core-Objects mapping](https://github.com/NYPL-discovery/discovery-api/blob/3e0eaacbdc718ab3d0733d4a7f51baeb7f6a0918/lib/delivery-locations-resolver.js#L37)
1. The list of delivery locations is also [modified to use the location labels that NYPL Core prefers](https://github.com/NYPL-discovery/discovery-api/blob/2267102369b01caf3bfa851e37c282c080fd956f/lib/location_label_updater.js#L15)
1. The list of delivery locations returned by above is also filtered based on what locations the patron's ptype allows based on [what `accessibleDeliveryLocationTypes` that ptype has in NYPL Core's patron-types document](https://github.com/NYPL-discovery/discovery-api/blob/3e0eaacbdc718ab3d0733d4a7f51baeb7f6a0918/lib/available_delivery_location_types.js#L14-L15)

**Requestability**

Individual item requestability (i.e. whether or not to show the 'Request' button depends on a NYPL Core lookup:

The API [checks an item's holding location against NYPL Core to determine if the location is "requestable"](https://github.com/NYPL-discovery/discovery-api/blob/2267102369b01caf3bfa851e37c282c080fd956f/lib/requestability_determination.js#L15). It also [checks an item's status as returned from Elasticsearch against NYPL Core's statuses document to determine if the status is "requestable"](https://github.com/NYPL-discovery/discovery-api/blob/2267102369b01caf3bfa851e37c282c080fd956f/lib/requestability_determination.js#L23)

### Discovery API Indexer

The DiscoveryApiIndexer builds ElasticSearch documents (and posts them to ES). To do so, it uses special "field mapping" files, which live inside NYPL Core (but are not JSON-LD). The field mapping files provide the link between MARC fields, DiscoveryStore predicates, and their ultimate "JSON-LD Key". Essentially, these mappings centrally associate "the data we want" with where in bib/item MARC documents it can be found.

See [this explanation in NYPL Core](https://github.com/NYPL/nypl-core/tree/master/mappings/recap-discovery)

### Discovery Store Poster

The DiscoveryStorePoster [uses NYPL Core Objects a lot](https://github.com/NYPL-discovery/discovery-store-poster/blob/06db246d4a3ba95e37c6cdb5479e3a493e259561/lib/serializers/item.js), mainly to validate and get labels for data it finds in item/bib records.

It also [uses the "field mapping" files](https://github.com/NYPL-discovery/discovery-store-poster/blob/06db246d4a3ba95e37c6cdb5479e3a493e259561/README.md#nypl-core-changes) to determine what MARC queries to run on bib/item records, and what predicates to use to store the extracted data.

### Recap Hold Request Consumer

The RecapHoldRequestConsumer [uses NYPL Core Objects' `by-recap-customer-code` lookup](https://github.com/NYPL/recap-hold-request-consumer/blob/bb8b00c46552c250b6c1b2bc7af245b4d0664978/models/location.rb#L5-L22) to translate incoming SCSB locations (customer codes) into their equivalent Sierra location code.

### Patron Eligibility Service

The PatronEligibilityService was recently updated to consider one's ptype when determining eligibility for placing holds. The service includes a check to [determine what `accessibleDeliveryLocationTypes` are valid for the ptype](https://github.com/NYPL-discovery/patron-eligibility-service/blob/c349a08308eda8e39426a6e6578c64b9eb5662a8/checkEligibility.js#L99). Typically, one's ptype includes either 'Research' or 'Research' and 'Scholar'. For two restricted ptypes (120 and 121), we've removed both values to indicate that patrons with those ptypes are not permitted to request items to any location.
