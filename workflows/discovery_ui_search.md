# NYPL Discovery UI Search Architecture

Please see diagram at: [TBD]

This workflow shows the steps for searching an item, patron log in, choosing a delivery location, and being ready to submit a hold request on NYPL's [Discovery UI](https://www.nypl.org/research/collections/shared-collection-catalog) as known as Shared Collection Catalog. The QA tier is [here](https://qa-www.nypl.org/research/collections/shared-collection-catalog).

For the workflow after submitting a hold request, please see [Patron Hold Request](workflows/patron_hold_request.md).

# Discovery UI Search Process Summary

This summary will be using Production tier as the example, but QA tier should be similiar.

## Search for Bibs

1. Visit [NYPL Shared Collection Catalog](https://www.nypl.org/research/collections/shared-collection-catalog). In the search form, change different search field and enter the search keyword. Then, press "Search" button.

1. Discovery UI sends two requests to Discovery API.
    1. First is the request for getting the list of bibs that fits the search request.

        The query string of the request is constructured as below,

        1. q=`search keywords`
        2. &filters[`filter category`][`the index of the filter in the same filter category`]=`filter value`
        3. &sort=`the condition to sort the results`&sort_direction=`the diretion to sort`
        4. &search_scope=`the field chosed with the dropdown from the search form`
        5. &page=`the start page of the result list. default is 1`

        For example, a possible query could be
        `q=puppy&filters[materialType][0]=resourcetypes%3Aaud&filters[materialType][1]=resourcetypes%3Amov&sort=title&sort_direction=asc&search_scope=title`

        It then sends to `https://platform.nypl.org/api/v0.1/discovery/resources?q=puppy&filters[materialType][0]=resourcetypes%3Aaud&filters[materialType][1]=resourcetypes%3Amov&sort=title&sort_direction=asc&search_scope=title&per_page=50`

        Notice that `&per_page=50` means it returns the results divided by 50 items per page and it is hard coded in Discovery UI.

    1. The second request is the request for the possible filters of the results from the first requests. For example, with the keyword `puppy`, the results could provide the filters of different languages and materials types for the user to refine the search results of searching `puppy`.

        The query string for the second request is constructured as below,

        1. q=`search keywords`
        2. &filters[`filter category`][`the index of the filter in the same filter category`]=`filter value`
        3. &search_scope=`the field chosed with the dropdown from the search form`

        For example, a possible query could be
        `q=puppy&filters[materialType][0]=resourcetypes%3Aaud&filters[materialType][1]=resourcetypes%3Amov&search_scope=title`

        It then sends to `https://platform.nypl.org/api/v0.1/discovery/resources/aggregations?q=puppy&filters[materialType][0]=resourcetypes%3Aaud&filters[materialType][1]=resourcetypes%3Amov&search_scope=title`

1. Discovery API then sends the two requests in order to Elasticsearch discovery-api-production. Then it returns both the responses from Elasticsearch back to Disovery UI. Discovery UI redirects the user to the search result page with the result items listed. The search result page has the URI constructed with the search query, for example,
`https://www.nypl.org/research/collections/shared-collection-catalog/search?q=puppy&filters[materialType][0]=resourcetypes%3Aaud&filters[materialType][1]=resourcetypes%3Amov&sort=title&sort_direction=asc&search_scope=title`

## Look up a Bib

1. On search result page, Discovery UI parses the result and lists all the bibs. If a bib has available items, it will display the "Request" button for the first available item.

1. If the user clicks the "Request" button, Discovery UI will then proceed to the workflow of requesting a hold. Please see the workflow in "Place a Hold" section.

1. If the user clicks the bib's title, Discovery UI makes two requests to Discovery API with the bib's bib ID.

    1. First, the request to get the bib's detailed data in JSON. The example request query could be as this, /discovery/resources/`Bib's ID`. Therefore, the whole endpoint requested will be,
    `https://platform.nypl.org/api/v0.1/discovery/resources/b15874032`

    1. Second, Discovery UI sends the request to get annotated-marc formatting of detailed information for the Bib. The query, for example, could be /discovery/resources/`Bib's ID and add .annotated-marc`. Therefore, the whole endpoint requested will be,
    `https://platform.nypl.org/api/v0.1/discovery/resources/b15874032.annotated-marc`

1. Discovery API will then send the two requests to Elasticsearch discovery-api-production and return the responses back to Discovery UI. Discovery UI will assign the second response of annotated-marc formatting information to the first respons of JSON fomatting. The user then will be redirected to the bib page, such as
`https://www.nypl.org/research/collections/shared-collection-catalog/bib/b15874170#tab1`

## Place a Hold

1. If the bib has available items, it will lists all the available items each with a "Request" button in the bib page or the just the first one in search result page. By clicking the "Request" button, Discovery UI will send three requests to Discovery API for possible delivery locations. The query will be constructed with the bib ID and item ID.

1. Before doing so, Discovery UI first will check if the cookie `nyplIdentityPatron` exists. If so, it will then proceed to use JWT to decode the cookie for the user's patron ID. It then will call https://platform.nypl.org/api/v0.1/patron/`Patron's ID` to get the user's patron information and stroe it in res.locals.data. It also save the patron ID in the request object.

1. If there's no cookie `nyplIdentityPatron`, which means the user has not logged in yet, Discovery UI will just store the same object with empty values.

1. Before sending the request to put a hold on an item, Discovery UI will check if there's a valid patron ID in the request object. If yes, it will proceed the request. If no, it will then redirect the user to log in to the endpoint, https://login.nypl.org/auth/login?redirect_uri=`The original request endpont of the request button`.

1. After logged in, Discovery UI sends the three requests to Discovery API.

    1. First, the request to get the bib's detailed data in JSON. The example request query could be as this, /discovery/resources/`Bib's ID`. Therefore, the whole endpoint requested will be,
    `https://platform.nypl.org/api/v0.1/discovery/resources/b15874032`

    1. Second, Discovery UI sends the request to get annotated-marc formatting of detailed information for the Bib. The query, for example, could be /discovery/resources/`Bib's ID and add .annotated-marc`. Therefore, the whole endpoint requested will be,
    `https://platform.nypl.org/api/v0.1/discovery/resources/b15874032.annotated-marc`

    1. Last, Discovery UI, based on the responses it gets from the two previous requests, it sends the request to Discovery API to get available delivery locations with the user's patron ID and the item's barcode. The endpoint is constructed as such
    https://platform.nypl.org/api/v0.1/request/deliveryLocationsByBarcode?barcodes[]=`item's barcode`&patronId=`the user's patron ID`.

1. Discovery API first calls https://platform.nypl.org/api/v0.1/`patron's ID` to get the patron's PType, and then map the PType with NYPL Core's sheet to get available delivery locations.

  Note that even if there's no available PType or the PType is not on NYPL Core yet, Discovery API will still return a default set of delivery locations, which are those the Research PType has. The reason why it is doing this is to avoid users with a new PType from being unable to request a hold before the PType is added to NYPL Core. However, if the PType is not allowed to put the hold, then the hold request will never be executed by Sierra. At this moment, we don't have this kind of PType, yet we do not have any mechanism to alert the users if this happened either.

  A patron's PType will affect the permission to put the hold on and check out an item. The library assigns the PType to a patron based on the age, living locations, the patron's organization and etc. To know more about the current PTypes we have on NYPL Core, please visit this link,
  https://github.com/NYPL/nypl-core/blob/master/vocabularies/csv/patronTypes.csv

1. Based on the responses from Discovery API, Discovery UI will then redirect the user to the hold page. At the page, the user can choose one of the delivery locations or electronic documents (if availabe) and then click "Submit Request" to place the hold.
