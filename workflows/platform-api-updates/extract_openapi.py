import json
import boto3
from fastapi.openapi.utils import get_openapi
from index import app  # Import your FastAPI instance

# SET YOUR CONFIG HERE
LAMBDA_FUNCTION_NAME = "name-of-lambda"
REGION = "us-east-1"  # e.g., us-east-1


def get_lambda_arn(function_name):
    client = boto3.client('lambda', region_name=REGION)
    response = client.get_function(FunctionName=function_name)
    return response['Configuration']['FunctionArn']


def generate_spec():
    # 1. Get real AWS data
    try:
        lambda_arn = get_lambda_arn(LAMBDA_FUNCTION_NAME)
        # Construct the specialized API Gateway Invocation URI
        uri = f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
    except Exception as e:
        print(f"Error fetching Lambda ARN: {e}")
        return

    # 2. Generate the standard FastAPI OpenAPI schema
    openapi_schema = get_openapi(
        title="Lists-Service-QA",
        version="1.0.0",
        openapi_version="3.0.3",  # <--- CRITICAL: Force 3.0.3 for AWS
        routes=app.routes,
    )

    # 3. Define the AWS Integration object
    aws_integration = {
        "type": "aws_proxy",
        "httpMethod": "POST",  # Lambda proxy integrations ALWAYS use POST for the trigger
        "uri": uri,
        "passthroughBehavior": "when_no_match"
    }

    # 4. Inject the extension into every path/method
    for path in openapi_schema.get("paths", {}):
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["x-amazon-apigateway-integration"] = aws_integration

    # 5. Write the final JSON
    with open("openapi_ready.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)

    print(
        f"Successfully generated openapi_ready.json for Lambda: {LAMBDA_FUNCTION_NAME}")


if __name__ == "__main__":
    generate_spec()
