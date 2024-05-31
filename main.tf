provider "archive" {}
data "archive_file" "lambda_zip_file" {
  type        = "zip"
  source_dir  = "source/"
  output_path = "lambda/config_lambda.zip"
}

resource "aws_lambda_function" "get_members_lambda" {
  function_name    = "Get-${var.solution_name}"
  filename         = data.archive_file.lambda_zip_file.output_path
  role             = aws_iam_role.lambda_role.arn
  handler          = "GetMembers.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_zip_file.output_base64sha256
  timeout          = 900
  environment {
    variables = {
      "DynamoDB" = var.SCPdynamoDB
      "DynamoDBRole" = var.SecTooling_DDB_Role_Arn
    }
  }
}

resource "aws_lambda_function" "apply_exclusion_lambda" {
  function_name    = "Deploy-${var.solution_name}"
  filename         = data.archive_file.lambda_zip_file.output_path
  role             = aws_iam_role.lambda_role.arn
  handler          = "CFNStackSetOperations.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_zip_file.output_base64sha256
  timeout          = 900
  environment {
    variables = {
      "TemplateURL"  = var.template_url
      "StackSetName" = var.stack_set_name
    }
  }
}

resource "aws_lambda_function" "check_execution_lambda" {
  function_name    = "Check-${var.solution_name}"
  filename         = data.archive_file.lambda_zip_file.output_path
  role             = aws_iam_role.lambda_role.arn
  handler          = "CheckExecution.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_zip_file.output_base64sha256
  timeout          = 900
}

resource "aws_lambda_function" "start_execution_lambda" {
  function_name    = "StartExecution-${var.solution_name}"
  filename         = data.archive_file.lambda_zip_file.output_path
  role             = aws_iam_role.lambda_role.arn
  handler          = "StartExecution.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_zip_file.output_base64sha256
  timeout          = 900
  environment {
    variables = {
      "StateMachineArn" = aws_sfn_state_machine.cloudformation_operations.arn
    }
  }
  depends_on = [aws_sfn_state_machine.cloudformation_operations]
}


resource "aws_lambda_permission" "execution_lambda_invoke" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.start_execution_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.bucket_name}"
  source_account = var.SecurityToolingAccountId
  statement_id  = "AllowS3Invoke"
}

data "template_file" "statemachine_tpl" {
  template = file("${path.module}/StateMachine.json")
  vars = {
    GetMembers     = aws_lambda_function.get_members_lambda.arn
    CFNOperation  = aws_lambda_function.apply_exclusion_lambda.arn
    CheckExecution = aws_lambda_function.check_execution_lambda.arn
  }
}

resource "aws_sfn_state_machine" "cloudformation_operations" {
  name_prefix = var.solution_name
  role_arn    = aws_iam_role.state_machine_role.arn
  definition  = data.template_file.statemachine_tpl.rendered

}

resource "aws_cloudwatch_log_group" "get_lambda_loggroup" {
  name              = "/aws/lambda/Get-${var.solution_name}"
  retention_in_days = 30
}
resource "aws_cloudwatch_log_group" "apply_lambda_loggroup" {
  name              = "/aws/lambda/Apply-${var.solution_name}"
  retention_in_days = 30
}
resource "aws_cloudwatch_log_group" "check_lambda_loggroup" {
  name              = "/aws/lambda/Check-${var.solution_name}"
  retention_in_days = 30
}
