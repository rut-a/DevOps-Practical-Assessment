provider "aws" {
  region = "us-east-1"
  access_key = "test"
  secret_key = "test"

  endpoints {
    s3 = "http://localhost:4566"
    sqs = "http://localhost:4566"
    lambda = "http://localhost:4566"
    iam = "http://localhost:4566"
  }

  skip_credentials_validation = true
  skip_metadata_api_check = true
  s3_use_path_style = true
  skip_requesting_account_id = true

}  
