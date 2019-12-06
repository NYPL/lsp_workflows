
# Things that depend on NYPL-Core

## Discovery API

### Delivery Locations By Barcode

The Discovery API serves a delivery-locations-by-barcode endpoint for determining the delivery locations available to a patron for a specific item. It's used by the DiscoveryFrontEnd to display available delivery options.

For an overview of how the options are computed, [see this section of the workflow on SCSB Locations](https://github.com/NYPL/lsp_workflows/blob/18953c472cd9ad5f626040e7bbc7f1bc9fcd706e/workflows/add_scsb_location.md#a-note-on-the-holding-delivery-location-relationship)

1. The list of delivery locations is developed by examining the item's customer code (as returned by SCSB API) and using that as a key into the `by-recap-customer-code` NYPL-Core-Objects mapping](https://github.com/NYPL-discovery/discovery-api/blob/3e0eaacbdc718ab3d0733d4a7f51baeb7f6a0918/lib/delivery-locations-resolver.js#L37)
1. The list of delivery locations is also [modified to use the location labels that NYPL Core prefers](https://github.com/NYPL-discovery/discovery-api/blob/2267102369b01caf3bfa851e37c282c080fd956f/lib/location_label_updater.js#L15)
1. The list of delivery locations returned by above is also filtered based on what locations the patron's ptype allows based on [what `accessibleDeliveryLocationTypes` that ptype has in NYPL Core's patron-types document](https://github.com/NYPL-discovery/discovery-api/blob/3e0eaacbdc718ab3d0733d4a7f51baeb7f6a0918/lib/available_delivery_location_types.js#L14-L15)

### Requestability

Individual item requestability (i.e. whether or not to show the 'Request' button depends on a NYPL Core lookup:

The API [checks an item's holding location against NYPL Core to determine if the location is "requestable"](https://github.com/NYPL-discovery/discovery-api/blob/2267102369b01caf3bfa851e37c282c080fd956f/lib/requestability_determination.js#L15). It also [checks an item's status as returned from Elasticsearch against NYPL Core's statuses document to determine if the status is "requestable"](https://github.com/NYPL-discovery/discovery-api/blob/2267102369b01caf3bfa851e37c282c080fd956f/lib/requestability_determination.js#L23)

## Discovery Front End

DiscoveryFrontEnd has a funny relationship with NYPL-Core. It does not use it directly but does maintain its own static hash of location data that must be in agreement with entries in NYPL Core. This is not an ideal situation. [Best described here](https://github.com/NYPL-discovery/discovery-front-end/blob/9a32fccd212fc644503ed0e516f59e254340f335/README.md#adding-locations)

## Discovery API Indexer

The DiscoveryApiIndexer builds ElasticSearch documents (and posts them to ES). To do so, it uses special "field mapping" files, which live inside NYPL Core (but are not JSON-LD). The field mapping files provide the link between MARC fields, DiscoveryStore predicates, and their ultimate "JSON-LD Key". Essentially, these mappings centrally associate "the data we want" with where in bib/item MARC documents it can be found.

See [this explanation in NYPL Core](https://github.com/NYPL/nypl-core/tree/master/mappings/recap-discovery)

## Discovery Store Poster

The DiscoveryStorePoster [uses NYPL Core Objects a lot](https://github.com/NYPL-discovery/discovery-store-poster/blob/06db246d4a3ba95e37c6cdb5479e3a493e259561/lib/serializers/item.js), mainly to validate and get labels for data it finds in item/bib records.

It also [uses the "field mapping" files](https://github.com/NYPL-discovery/discovery-store-poster/blob/06db246d4a3ba95e37c6cdb5479e3a493e259561/README.md#nypl-core-changes) to determine what MARC queries to run on bib/item records, and what predicates to use to store the extracted data.

## Recap Hold Request Consumer

The RecapHoldRequestConsumer [uses NYPL Core Objects' `by-recap-customer-code` lookup](https://github.com/NYPL/recap-hold-request-consumer/blob/bb8b00c46552c250b6c1b2bc7af245b4d0664978/models/location.rb#L5-L22) to translate incoming SCSB locations (customer codes) into their equivalent Sierra location code.

