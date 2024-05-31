terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.39.1"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

terraform {
  backend "s3" {
    bucket = "jenkins-cloudops-terraform-state"
    key    = "aws-cloudformation-operations-deployment/terraform_state"
    region = "us-east-1"
  }
}
