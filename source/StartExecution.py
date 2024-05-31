import boto3
import logging
import json
import os


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def start_execution(state_machine_arn):
    client = boto3.client('stepfunctions')
    # Start the execution of the state machine
    execution_response = client.list_executions(
        stateMachineArn=state_machine_arn,
        statusFilter='RUNNING'
        )['executions']
    if execution_response:
        logger.info("%s State Machine execution in progress, skipping new execution", state_machine_arn)
    else:
        response = client.start_execution(
            stateMachineArn=state_machine_arn,
            input='{}'  # Replace with the input data for your state machine (JSON format)
        )
        execution_arn = response['executionArn']
        logger.info("execution started ID: %s", execution_arn)
        return {
            'statusCode': 200,
            'body': f'Started execution: {execution_arn}'
        }


def lambda_handler(event, context):
    logger.info("%s event", event)
    state_machine_arn = os.environ["StateMachineArn"]
    start_execution(state_machine_arn)
