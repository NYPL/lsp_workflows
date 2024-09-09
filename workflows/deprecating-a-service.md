# Deprecating a Service

When a service has little or no usage, based on AWS Lambda invocations, and we can verify that no one is using the service, we can begin the decommissioning process. The Engineering General repo has information on [decommissioning](https://github.com/NYPL/engineering-general/blob/main/standards/decommissioning.md) which serves as a starting point.

In addition to the above process, the following steps need to be performed to decommission a service.

## Documentation Updates

- Create a PR that adds a deprecate note in the service's Github repo.
- Create a PR to remove the Swagger document endpoints from the [`docsservice`](https://github.com/NYPL/docsservice) repo. Make sure you target both the QA and production environments by updating the `config/var_qa.env` and `config/var_production.env` files.
- Once all steps are complete, go to the repo's settings and click on "Archive this repository" to set it as read-only.

## API Gateway

- In the AWS API Gateway dashboard, target the endpoint that the service previously supported. Delete the resource which will delete all children method execution endpoints (such as GET and POST).
- In the same dashboard, delete the relevant `/docs` resource.
- Deploy the update to the QA stage and then production.

## Lambda

- In the AWS Lambda dashboard, find the service that is no longer used and delete the function. Make sure both the QA and production functions are deleted.

## Team

- Let the team know that this process is complete.