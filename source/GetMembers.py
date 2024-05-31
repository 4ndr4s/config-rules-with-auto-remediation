import logging
import os
import sys
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Constants
DEFAULT_REGION = 'us-east-1'


def lambda_handler(event, context):
    role_arn = os.environ["DynamoDBRole"]
     # Assume role
    sts_client = boto3.client("sts")
    assumed_role_object = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="AWSStateMachineRoleForDDB")
    credentials = assumed_role_object["Credentials"]

    # Create DynamoDB Resource
    dynamodb_resource = boto3.resource(
        "dynamodb",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name = DEFAULT_REGION
    )
    table = dynamodb_resource.Table(os.environ["DynamoDB"])
    response = table.scan()["Items"]
    return {
        "statusCode": 200,
        "members": response,
    }
