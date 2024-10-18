data "aws_iam_policy_document" "state_machine_policy" {
  statement {
    sid    = "StateMachinePolicyId"
    effect = "Allow"
    principals {
      identifiers = ["states.amazonaws.com"]
      type        = "Service"
    }
    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "state_machine_policy_doc" {
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction",
      "lambda:Get*",
      "lambda:List*"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "state_machine_execution_policy" {
  name   = "${var.solution_name}-state-machine-policy"
  policy = data.aws_iam_policy_document.state_machine_policy_doc.json
}

resource "aws_iam_role" "state_machine_role" {
  name               = "${var.solution_name}-state-machine-role"
  assume_role_policy = data.aws_iam_policy_document.state_machine_policy.json
}

resource "aws_iam_role_policy_attachment" "state_machine_policy_attachment" {
  role       = aws_iam_role.state_machine_role.name
  policy_arn = aws_iam_policy.state_machine_execution_policy.arn
}

## Lambda role
data "aws_iam_policy_document" "lambda_policy_sts" {
  statement {
    sid    = "SecHubConfigLambdaPolicyId"
    effect = "Allow"
    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }
    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "lambda_policy_doc" {
  statement {
    effect = "Allow"

    actions = [
      "sts:AssumeRole"
    ]
    resources = [var.SecTooling_DDB_Role_Arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:Scan",
      "dynamodb:Query",
      "dynamodb:GetItem"
    ]
    resources = ["arn:aws:dynamodb:us-east-1:${var.SecurityToolingAccountId}:table/${var.SCPdynamoDB}"]
  }
  statement {
    effect = "Allow"
    actions = [
        "cloudformation:CreateStackSet",
        "cloudformation:UpdateStackSet",
        "cloudformation:DescribeStackSet",
        "cloudformation:ListStackInstances",
        "cloudformation:CreateStackInstances",
        "cloudformation:UpdateStackInstances",
        "cloudformation:DescribeStackSetOperation",
        "cloudformation:DeleteStackInstances",
        "cloudformation:TagResource"
    ]
    resources = ["*"]
  }
  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = ["arn:aws:s3:::${var.bucket_name}", "arn:aws:s3:::${var.bucket_name}/*"]
  }
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["*"]
  }
  statement {
    effect = "Allow"

    actions = [
      "states:StartExecution",
      "states:ListExecutions"
    ]

    resources = [aws_sfn_state_machine.cloudformation_operations.arn]
  }

}

resource "aws_iam_policy" "lambda_policy" {
  name   = "${var.solution_name}-lambda-policy"
  policy = data.aws_iam_policy_document.lambda_policy_doc.json
}

resource "aws_iam_role" "lambda_role" {
  name               = "${var.solution_name}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_policy_sts.json
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}