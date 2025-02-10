variable "aws_region" {
  default = "us-east-1"
}

variable "solution_name" {
  default = "CFN-StackSet-Deployment"
}
variable "bucket_name" {
  default = "bucket Name"
}
variable "tags" {
  type        = map(any)
  description = "An object of tag key value pairs"
  default = {
    solution-name = "CloudFormationStackSetDeployment"
  }
}
variable "SCPdynamoDB" {
  default = "dynamoDB table that stores regions per account"
}
variable "trusted_role_arn" {
  default = "Execute-Operations-Role"
}
variable "SecurityToolingAccountId" {
  default = 412090077236
}
variable "template_url" {
  default = "https://s3.amazonaws.com/<bucket name>/aws-org-config-rules/base.yaml"

}
variable "stack_set_name" {
  default = "AWS-Config-Rules"

}
variable "SecTooling_DDB_Role_Arn" {
  default = "<Role ARN to read DDB table to get acounts and regions>"
}