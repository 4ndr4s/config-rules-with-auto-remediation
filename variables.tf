variable "aws_region" {
  default = "us-east-1"
}

variable "solution_name" {
  default = "FTA-CFN-StackSet-Deployment"
}
variable "bucket_name" {
  default = "scp-region-restriction-aaae72"
}
variable "tags" {
  type        = map(any)
  description = "An object of tag key value pairs"
  default = {
    solution-name = "FortraCloudFormationStackSetDeployment"
  }
}
variable "SCPdynamoDB" {
  default = "scp-region-restriction-75032c"
}
variable "trusted_role_arn" {
  default = "FTA-Execute-Operations-Role"
}
variable "SecurityToolingAccountId" {
  default = 412090077236
}
variable "template_url" {
  default = "https://s3.amazonaws.com/securitytooling-terraform-state/aws-org-config-rules/base.yaml"

}
variable "stack_set_name" {
  default = "FTA-AWS-Config-Rules"

}