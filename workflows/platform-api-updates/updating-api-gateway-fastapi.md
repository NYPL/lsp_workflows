# `fastapi` and `aws-cli` workflow
If your app is a python app developed using `fastapi`, leverage the open api json generator. 

## Steps:
### 1. Extract openapi json
Using the AI-generated (Gemini webapp) script `./extract_openapi.py` for reference, generate the open api spec for your changes. If you want the endpoints to point to the correct environment per stage, for now you will have to manually add `${stageVariables.environment}` to the `uri` property in `x-amazon-apigateway-integration`. This is because OpenAPI validation prohibits curly braces. For example:
```
        "x-amazon-apigateway-integration": {
          "type": "aws_proxy",
          "httpMethod": "POST",
          "uri": "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:946183545209:function:ListsService-${stageVariables.environment}/invocations",
          "passthroughBehavior": "when_no_match"
        }
```

### 2. PUT the changes to the API Gateway
With the aws cli installed, and once you have authenticated, run the following:
```
aws apigateway put-rest-api  \
    --rest-api-id {API GATEWAY ID} \
    --mode merge \
    --body file://{PATH_TO_OPENAPI.JSON} \
    --cli-binary-format raw-in-base64-out
```

### 3. Update permissions for the lambda 
See instructions [here](https://github.com/NYPL/aws/blob/master/common/apigateway.md)
Note statement-id can be unique string.