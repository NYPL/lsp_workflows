# Add SCSB Location

This document describes how to make recently added Sierra locations usable as delivery locations in SCC.

## Overview

Note the following is a targetted distillation of information in [Discovery Properties](https://docs.google.com/spreadsheets/d/1qTjXqCO4eusaxr6MGpb7ns4u6k8hmg0s6LzJWvHhmHI/edit#gid=493047939).

There are two different kinds of locations:
 * locations (aka Sierra locations): These are locations found in Sierra
 * ReCAP locations (aka customer codes): These *map to* Sierra locations (and all other partner locations)

It may be useful to preface this with: within the domain of "locations" (and among ReCAP locations) there are two disjoint categories of location that emerge from how they are used:
 * Holding locations: Locations that are referenced directly from an item indicate the location where the physical item is stored. The holding location links to zero or more delivery locations.
 * Delivery locations: Locations to which one may request that an item be sent. Delivery locations are never also holding locations. The set of delivery locations for an item is the set of delivery locations referenced by the item's holding location.

## To add a location, first gather some information

For each location you'll add, you should gather the following:

* **Sierra location code**: Three-four character code uniquely identifying the location in Sierra (e.g. 'mal', 'sce')
* **Label (skos:prefLabel)**: Full name of location shown to staff & patrons in SCC (e.g. "Schwarzman Building - Main Reading Room 315", "Schomburg Center - Photographs & Prints")
* **Sierra label (skos:altLabel)**: A slightly shorter label used by Sierra (e.g. "SASB - Service Desk Rm 315", "Schomburg Prints & Photographs")
* **Parent location (dcterms:isPartOf)**: Typically two-character code identifying parent location (e.g. 'ma', 'sc') 
* **Delivery location type (nypl:deliveryLocationType)**: Must be 'Branch', 'Research', or 'Scholar' to indicate the class of patron that may have materials delivered to the location. Branch locations are 'Branch'. Everything else is 'Research' unless it's a designated 'Scholar' room.
* **Location Slug (nypl:locationsSlug)**: The "slug" identifying the record in the Locations API most relevant to this location. I believe this is largely a formality, not used. (e.g. 'general-research-division', 'schomburg')
* **Owner (nypl:owner)**: The NYPL center, division, branch, or unit responsible for the location (links into [NYPL-Core Organizations](https://github.com/NYPL/nypl-core/blob/master/vocabularies/json-ld/organizations.json)). (e.g. 'http://data.nypl.org/orgs/1000', 'http://data.nypl.org/orgs/1118')
* **Requestable (nypl:requestable)**: Boolean indicating whether items assigned this location can be requested *in SCC*. Note that this is meaningless (and thus `false`) for delivery locations because items are never assigned home locations that are also delivery locations. Requestable will be `true` only for those locations that are used as the "home" location of items in ReCAP that may be requested (e.g. 'rc', 'rc2cf', 'rc2cf')
* **Collection type (nypl:collectionType)**: The library collection, Research or Branch, that a location's items belong to. Used by the SCC data pipeline as one of a few checks used to determine if an item is "research" or "branch". A location might contain items from both collections.


* **ReCAP customer code**: This uniquely identifies the location in ReCAP. All customer codes map to a single NYPL/partner location. Customer codes tend to be minted after a new Sierra location is created/proposed. (e.g. 'NH', 'SP')
* **ReCAP Label**: Label used by ReCAP. Mostly for documentation purpose; Not shown in any interface. (e.g. "SASB Rose Main Reading Room", "Schomburg Prints & Photographs")
* **ReCAP locations that may deliver to this location**: The set of ReCAP locations (customer codes) whose items may be delivered to this location.
* **ReCAP locations that items at this location may deliver to**: Less commonly, if the location added is assigned as the `customerCode` (i.e. home location) of an item, to what locations may that item be delivered?

## Add entries to NYPL-Core

Having collected the above information, add the relevant data to [locations.csv](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/locations.csv), [locations.json](https://github.com/NYPL/nypl-core/blob/master/vocabularies/json-ld/locations.json), [recapCustomerCodes.csv](https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/recapCustomerCodes.csv), and [recapCustomerCodes.json](https://github.com/NYPL/nypl-core/blob/master/vocabularies/json-ld/recapCustomerCodes.json).

