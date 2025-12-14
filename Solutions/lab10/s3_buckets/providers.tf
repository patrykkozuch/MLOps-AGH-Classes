terraform {
  required_version = ">=1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    region = "us-east-1"
    bucket = "agh-mlops-aws-lab-tf"
    key    = "mlops-lab10-ex2/terraform.tfstate"
  }
}


provider "aws" {
  profile = "default"
  alias   = "us_east_1"
  region  = "us-east-1"
}

provider "aws" {
  profile = "default"
  region  = "us-west-2"
  alias   = "us_west_2"
}