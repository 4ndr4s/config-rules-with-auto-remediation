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
        else:
            raise e
    return response


def create_stack_set(client, stack_set, template):
    try:
        response = client.create_stack_set(
            StackSetName=stack_set,
            Description='StackSet to deploy AWS Config Rules per account in designated regions',
            Capabilities=[ 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND' ],
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


def update_stack_set(client, stack_set, template):
    try:
        response = client.update_stack_set(
            StackSetName=stack_set,
            Description='StackSet to deploy AWS Config Rules per account in designated regions',
            TemplateURL=template,
            UsePreviousTemplate=False,
            Capabilities=[ 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND' ],
            OperationPreferences={
                'RegionConcurrencyType': 'PARALLEL',
                'FailureTolerancePercentage': 100,
                'MaxConcurrentCount': 1
            },
            CallAs='SELF',
            Tags=[
                {
                    'Key': 'FTA-Project',
                    'Value': 'AWSConfigRules'
                },
            ],
            ManagedExecution={'Active': True}
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            logger.info("StackSet Not Found.")
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


def describe_stack_set_instance(client, stack_set, account_id, aws_region):
    try:
        while True:
            response = client.describe_stack_instance(
                StackSetName=stack_set,
                StackInstanceAccount=account_id,
                StackInstanceRegion=aws_region,
                CallAs='SELF'
            )
            stack_instance_status = response['StackInstance']['StackInstanceStatus']['DetailedStatus']
            if stack_instance_status == 'RUNNING' or stack_instance_status == 'PENDING':
                time.sleep(60)
            else:
                return stack_instance_status
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            logger.info("StackSetNotFoundException not found.")
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
    """
    Lambda function handler for managing CloudFormation StackSets.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.

    Returns:
        dict: The response containing the status code and account information.

    Raises:
        KeyError: If required environment variables are not set.
    """
    logger.info(event)
    account_id, regions = event["account"], event["regions"]
    template_url = os.environ["TemplateURL"]

    # Create CloudFormation client
    cfn_client = boto3.client(
        "cloudformation",
        region_name=DEFAULT_REGION
    )
    stack_instances_status = list()

    # Check stack set status
    stack_set_name = os.environ["StackSetName"] + "-" + account_id
    stack_set_status = describe_stack_set(cfn_client, stack_set_name)

    # Handle stack set status
    if stack_set_status == 'StackSet not found':
        create_stack_set(cfn_client, stack_set_name, template_url)
        time.sleep(20)
        stack_set_status = describe_stack_set(cfn_client, stack_set_name)
        if stack_set_status['StackSet']['Status'] == 'ACTIVE':
            operation_id = create_stack_instances(cfn_client, account_id, regions, stack_set_name)['OperationId']
            if describe_stack_set_operation(cfn_client, stack_set_name, operation_id) == "SUCCEEDED":
                return {"statusCode": 200, "account": event["account"]}
            else:
                return {"statusCode": 500, "account": event["account"]}
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
                    for region in regions:
                        status = describe_stack_set_instance(cfn_client, stack_set_name, account_id, region)
                        stack_instances_status.append(status)
                    logger.info(f"{account_id} stack instances status: {stack_instances_status}")
                    if any(status != "SUCCEEDED" for status in stack_instances_status):
                        return {"statusCode": 500, "account": event["account"]}
                    return {"statusCode": 200, "account": event["account"]}
                else:
                    return {"statusCode": 500, "account": event["account"]}
        else:
            # operation_id = update_stack_instances(cfn_client, account_id, regions, stack_set_name)['OperationId']
            operation_id = update_stack_set(cfn_client, stack_set_name, template_url)['OperationId']
            if describe_stack_set_operation(cfn_client, stack_set_name, operation_id) == "SUCCEEDED":
                for region in regions:
                    status = describe_stack_set_instance(cfn_client, stack_set_name, account_id, region)
                    stack_instances_status.append(status)
                logger.info(f"{account_id} stack instances status: {stack_instances_status}")
                if any(status != "SUCCEEDED" for status in stack_instances_status):
                    return {"statusCode": 500, "account": event["account"]}
                return {"statusCode": 200, "account": event["account"]}
            else:
                return {"statusCode": 500, "account": event["account"]}
    else:
        logger.info("An error occurred:", stack_set_status)
        return {"statusCode": 500, "account": event["account"]}
