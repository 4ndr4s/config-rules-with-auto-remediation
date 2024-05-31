import unittest
import boto3
from unittest.mock import MagicMock, patch
from CFNStackSetOperations import lambda_handler

class TestLambdaHandler(unittest.TestCase):
    def test_lambda_handler(self):
        # Mock the event data
        event = {
            "account": "1234567890",
            "regions": ["us-east-1", "us-west-2"]
        }

        # Mock the environment variables
        with patch.dict('os.environ', {
            "TemplateURL": "https://s3.amazonaws.com/securitytooling-terraform-state/aws-org-config-rules/base.yaml",
            "MemberRole": "arn:aws:iam::1234567890:role/MemberRole",
            "StackSetName": "MyStackSet"
        }):
            # Mock the assume_role response
            sts_client_mock = MagicMock()
            sts_client_mock.assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "ACCESS_KEY_ID",
                    "SecretAccessKey": "SECRET_ACCESS_KEY",
                    "SessionToken": "SESSION_TOKEN"
                }
            }
            boto3.client = MagicMock(return_value=sts_client_mock)

            # Mock the describe_stack_set response
            cfn_client_mock = MagicMock()
            cfn_client_mock.describe_stack_set.return_value = {
                "StackSet": {
                    "Status": "ACTIVE",
                    "Regions": ["us-east-1", "us-west-2"]
                }
            }
            boto3.client = MagicMock(return_value=cfn_client_mock)

            # Call the lambda_handler function
            result = lambda_handler(event, None)

            # Assert the expected result
            self.assertEqual(result, {"statusCode": 200, "account": "1234567890"})

if __name__ == '__main__':
    unittest.main()