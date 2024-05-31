import logging
import os
import sys
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

dynamodb_resource = None


def lambda_handler(event, context):
    global dynamodb_resource
    if not dynamodb_resource:
        dynamodb_resource = boto3.resource("dynamodb")
    table = dynamodb_resource.Table(os.environ["DynamoDB"])
    response = table.scan()["Items"]
    return {
        "statusCode": 200,
        "members": response,
    }
