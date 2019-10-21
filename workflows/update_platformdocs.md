# Updating platformdocs.nypl.org

PlatformDocs provides interactive documentation on the Platform API. It consists of an instance of the Swagger UI configured a single Swagger doc (aka "Swagger JSON") representing all Platform API endpoints.

## I. Swagger UI

The Swagger UI is hosted from one of two S3 buckets in `nypl-digital-dev`:

 * QA (https://qa-platformdocs.nypl.org) is hosted from "qa-platformdocs.nypl.org"
 * Production (https://platformdocs.nypl.org) is hosted from "platformdocs.nypl.org"

Both S3 buckets are origins for CloudFront instances, which have CNAMEs 'qa-platformdocs.nypl.org' and 'platformdocs.nypl.org', respectively.

### Updating the Swagger UI

There is no NYPL repository for the Swagger UI. To update the Swagger UI:

 * Download the required Swagger UI release](https://github.com/swagger-api/swagger-ui/releases)
 * Unzip and navigate to the `dist` folder
 * Edit `index.html`, replacing the hardcoded swagger.json URL with "https://qa-platformdocs.nypl.org/api/list.json"
 * Upload the contents of the `dist` folder to the "qa-platformdocs.nypl.org" S3 bucket
 * Test and repeat for "platformdocs.nypl.org"

## II. Swagger JSON

We maintain a single Swagger JSON ([Open API Spec v2](https://swagger.io/specification/v2/)) that aggregates the individual Swagger JSONs from all endpoints in the Platform API. This is achieved via the [DocsService](https://github.com/NYPL/docsservice).

The DocsService has a `DOCS_URLS` environment variable, whose value is a comma-delimited list of URLs that serve Swagger docs. Each service in the Platform API is responsible for serving its own Swagger document. See documentation on [Adding a Platform API Endpoint](./adding-a-platform-api-endpoint.md#d-create-a-swagger-endpoint) for info on adding the docs route to your app. Once you have a working URL of the form `http://platform.nypl.org/api/v0.1/docs/your-app`, the next step is to register it with the DocsService to make your Swagger doc is a part of the greater, aggregated Swagger doc.

### Updating the Swagger JSON

To add your app's Swagger doc to PlatformDocs:

 * AWS Console > Lambda > "DocsService-qa"
 * Add your new docs endpoint to the `DOCS_URLS` environment variable (separated with a comma)
 * Issue an authenticated call on `https://qa-platform.nypl.org/api/v0.1/docs`
 * Check [https://qa-platformdocs.nypl.org/api/list.json](https://qa-platformdocs.nypl.org/api/list.json) to confirm your changes are correct
 * Repeat for production

### A little background on the DocsService

The DocsService has a single authenticated endpoint (`/api/v0.1/docs`), which does this:

1. fetches Swagger documents from all registered docs URLs (via a `DOCS_URLS` param)
2. merges them into a single Swagger document
3. uploads the result as "api/list.json" to an S3 bucket in `nypl-digital-dev` account
   - QA S3 bucket is "qa-platformdocs.nypl.org"
   - Production S3 bucket is "platform.nypl.org"

By issuing an authenticaticated `GET` on `/api/v0.1/docs`, you trigger the DocsService to rebuild the aggregated Swagger document for all registered services. You can perform that call from within PlatformDocs itself (or through Postman, or the [NYPL-Data-API-Client CLI](https://www.npmjs.com/package/@nypl/nypl-data-api-client), etc.)

If you don't mind waiting, docs are updated every 5 minutes automatically. This is achieved through the following means:

 * A CloudWatch "Rule" called "ColdStartPreventer-qa" and "ColdStartPreventer-production" runs on a fixed 5 minute schedule.*
 * The rule invokes a namesake Lambda ("ColdStartPreventer-qa" and "ColdStartPreventer-production")
 * The Lambda receives the event as a "CloudWatch Event"
 * The Lambda is configured with a `REQUEST_URLS` parameter that contains a comma-delimited list of values of the form: `URLPATH:CONCURRENCY`
 * For each `URLPATH` (e.g. "docs") and `CONCURRENCY` (e.g. `1`) combination, the ColdStartPreventer:
   * adds the configured `BASE_URL` to the beginning of the `URL` (producing URLs like "https://platform.nypl.org/api/v0.1/docs"
   * creates a pool of HTTP connections to the resulting URL with the stated concurrency (presumably, higher `CONCURRENCY` values ensure that - if there are multiple Lambda/server instances for a given endpoint - all of them process a request)
 * `docs:1` is one of ColdStartPreventer's configured `REQUEST_URLS`, meaning each invocation has the effect of issuing a single `GET` on `/api/v0.1/docs`, which occur every five minutes

 \* "ColdStartPreventer" rules and lambdas were created to keep certain Lambda endpoints "warm". Typically, when a Lambda is not invoked for a certain amount of time, [it's memory is "frozen" until the next invocation](https://docs.aws.amazon.com/lambda/latest/dg/running-lambda-code.html). When the next trigger comes in, it can take several seconds for the Lambda to be reconstituted. By issuing regular calls to endpoints serviced by specific Lambdas, we theoretically prevent those Lambdas from ever being frozen, ensuring that requests are snappy. The use of the "ColdStartPreventer" lambdas to hit a GET endpoint that rebuilds and uploads our Platform API Swagger doc is, admittedly, a bit of a hack.
