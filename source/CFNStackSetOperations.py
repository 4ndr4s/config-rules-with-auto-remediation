import logging
import sys
import boto3
import os
import botocore
import time

# Constants
DEFAULT_REGION = 'us-east-1'

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
sts_client = None


def describe_stack_set(client, stack_set):
    try:
        response = client.describe_stack_set(
            StackSetName=stack_set,
            CallAs='SELF'
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            logger.info("StackSet not found.")
            response = "StackSet not found"
        raise e
    return response


def create_stack_set(client, stack_set, template):
    try:
        response = client.create_stack_set(
            StackSetName=stack_set,
            Description='StackSet to deploy AWS Config Rules per account in designated regions',
            TemplateURL=template,
            Tags=[
                {
                    'Key': 'FTA-Project',
                    'Value': 'AWSConfigRules'
                },
            ],
            ManagedExecution={'Active': True}
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NameAlreadyExistsException':
            logger.info("StackSet already exists.")
        raise e
    return response


def create_stack_instances(client, account, regions, stack_set):
    try:
        response = client.create_stack_instances(
            StackSetName=stack_set,
            Accounts=[account],
            Regions=regions,
            OperationPreferences={
                'RegionConcurrencyType': 'PARALLEL',
                'FailureTolerancePercentage': 100,
                'MaxConcurrentCount': 1
            },
            CallAs='SELF'
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            logger.info("StackSet not found canceling.")
        raise e
    return response


def update_stack_instances(client, account, regions, stack_set):
    try:
        response = client.update_stack_instances(
            StackSetName=stack_set,
            Accounts=[account],
            Regions=regions,
            OperationPreferences={
                'RegionConcurrencyType': 'PARALLEL',
                'FailureTolerancePercentage': 100,
                'MaxConcurrentCount': 1
            },
            CallAs='SELF'
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            logger.info("StackSet not found canceling.")
        raise e
    return response


def describe_stack_set_operation(client, stack_set, operation):
    try:
        while True:
            response = client.describe_stack_set_operation(
                StackSetName=stack_set,
                OperationId=operation,
                CallAs='SELF'
            )
            operation_status = response['StackSetOperation']['Status']
            if operation_status == 'RUNNING' or operation_status == 'QUEUED':
                time.sleep(10)
            else:
                return operation_status
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'OperationNotFoundException':
            logger.info("OperationNotFoundException not found.")
        raise e


def delete_stack_instances(client, account, regions, stack_set):
    try:
        response = client.delete_stack_instances(
            StackSetName=stack_set,
            Accounts=[account],
            Regions=regions,
            OperationPreferences={
                'RegionConcurrencyType': 'PARALLEL',
                'FailureTolerancePercentage': 100,
                'MaxConcurrentCount': 1
            },
            CallAs='SELF',
            RetainStacks=False
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'OperationInProgressException':
            logger.info("OperationInProgressException not found.")
        raise e
    return response


def lambda_handler(event, context):
    logger.info(event)
    account_id, regions = event["account"], event["regions"]
    # template_url = "https://s3.amazonaws.com/securitytooling-terraform-state/aws-org-config-rules/base.yaml"
    template_url = os.environ["TemplateURL"]
    role_arn = os.environ["MemberRole"].replace("<accountId>", account_id)
    
    # Assume role
    sts_client = boto3.client("sts")
    assumed_role_object = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="AWSCloudformationRoleForConfigRules")
    credentials = assumed_role_object["Credentials"]

    # Create CloudFormation client
    cfn_client = boto3.client(
        "cloudformation",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name = DEFAULT_REGION
    )

    # Check stack set status
    stack_set_name = os.environ["StackSetName"]
    stack_set_status = describe_stack_set(cfn_client, stack_set_name)

    # Handle stack set status
    if stack_set_status == 'StackSet not found':
        create_stack_set(cfn_client, stack_set_name, template_url)
        stack_set_status = describe_stack_set(cfn_client, stack_set_name)
        if stack_set_status['StackSet']['Status'] == 'ACTIVE':
            create_stack_instances(cfn_client, account_id, regions, stack_set_name)
        else:
            logger.info(f"An error occurred: {stack_set_status}")
    elif stack_set_status['StackSet']['Status'] == 'ACTIVE':
        sort_regions = sorted(regions)
        sort_stack_regions = sorted(stack_set_status['StackSet']['Regions'])
        if sort_regions != sort_stack_regions:
            if len(sort_regions) < len(sort_stack_regions):
                delete_region = [region for region in sort_stack_regions if region not in sort_regions]
                operation_id = delete_stack_instances(cfn_client, account_id, delete_region, stack_set_name)['OperationId']
                if describe_stack_set_operation(cfn_client, stack_set_name, operation_id) == "SUCCEEDED":
                    return {"statusCode": 200, "account": event["account"]}
                else:
                    return {"statusCode": 500, "account": event["account"]}
            else:
                operation_id = create_stack_instances(cfn_client, account_id, regions, stack_set_name)['OperationId']
                if describe_stack_set_operation(cfn_client, stack_set_name, operation_id) == "SUCCEEDED":
                    return {"statusCode": 200, "account": event["account"]}
                else:
                    return {"statusCode": 500, "account": event["account"]}
        else:
            operation_id = update_stack_instances(cfn_client, account_id, regions, stack_set_name)['OperationId']
            if describe_stack_set_operation(cfn_client, stack_set_name, operation_id) == "SUCCEEDED":
                return {"statusCode": 200, "account": event["account"]}
            else:
                return {"statusCode": 500, "account": event["account"]}
    else:
        logger.info("An error occurred:", stack_set_status)
        return {"statusCode": 500, "account": event["account"]}
