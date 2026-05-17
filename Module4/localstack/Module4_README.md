# Module 4: Serverless File Processor (LocalStack)

## Overview

This project implements a serverless file processing system using LocalStack to simulate AWS infrastructure locally.

The system is designed to process `.json` files uploaded to an S3 bucket. Each upload triggers an AWS Lambda function that validates the JSON content and routes it to either an SQS queue (valid data) or a Dead Letter Queue (invalid data).

# Project Architecture

S3 Bucket (File Upload)
→ S3 Event Notification
→ AWS Lambda (File Processor)
→ JSON Validation
→ SQS Queue (Valid Messages)
→ Dead Letter Queue (Invalid Messages)

# 1. Environment Setup

## Create project directory

```bash
mkdir Module4
cd Module4
```

## Start LocalStack

```bash
docker compose up
```

## Terraform Initialization

```bash
cd file-processor/terraform
terraform init
```

# 2. File Processor Architecture

## Project Structure

```
file-processor/
├── lambda/
├── terraform/
├── test-files/
```

The system consists of three main parts:

- Terraform infrastructure definitions
- Lambda function for processing files
- Test JSON files for validation

# 3. Lambda Function Breakdown

### Section 1 — Imports & Clients

```python
import json
import boto3
import os

s3 = boto3.client("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL"))
sqs = boto3.client("sqs", endpoint_url=os.environ.get("AWS_ENDPOINT_URL"))

QUEUE_URL = os.environ["QUEUE_URL"]
DLQ_URL = os.environ["DLQ_URL"]
```

I import:

- `json` for parsing file content
- `boto3` for interacting with AWS services (S3, SQS)
- `os` for reading environment variables

The clients are configured to point to LocalStack using `AWS_ENDPOINT_URL`.

The environment variables define:

| Variable | Purpose |
|||
| `QUEUE_URL` | SQS queue for valid messages |
| `DLQ_URL` | Dead Letter Queue for invalid messages |



### Section 2 — Validation Logic

```python
def is_valid(payload):
    required_fields = ["id", "name"]
    return all(field in payload for field in required_fields)
```

This function validates incoming JSON data.

A file is considered valid only if it contains:

- `id`
- `name`

If any required field is missing, the payload is treated as invalid.

### Section 3 — Lambda Handler

```python
def lambda_handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        response = s3.get_object(Bucket=bucket, Key=key)
        body = json.loads(response["Body"].read())

        if is_valid(body):
            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(body)
            )
        else:
            sqs.send_message(
                QueueUrl=DLQ_URL,
                MessageBody=json.dumps(body)
            )

    return {"statusCode": 200}
```

This function handles the full processing workflow:

1. **Receive S3 event** — triggered when a `.json` file is uploaded.
2. **Extract bucket and object key** — identifies the uploaded file.
3. **Read file from S3** — retrieves the JSON object content.
4. **Parse JSON content** — converts file body into Python dictionary.
5. **Validate payload** — checks if required fields exist.
6. **Route message**
   - Valid → sent to SQS queue  
   - Invalid → sent to DLQ  
7. **Return success response**

# 4. Terraform Infrastructure Breakdown

## Section 1 — Provider Configuration

```hcl
provider "aws" {
  region     = "us-east-1"
  access_key = "test"
  secret_key = "test"

  endpoints {
    s3     = "http://localhost:4566"
    sqs    = "http://localhost:4566"
    lambda = "http://localhost:4566"
    iam    = "http://localhost:4566"
  }

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  s3_use_path_style           = true
  skip_requesting_account_id  = true
}
```

This configuration connects Terraform to LocalStack instead of real AWS.



## Section 2 — IAM Role

```hcl
resource "aws_iam_role" "lambda_role" {
  name = "lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}
```

This IAM role allows Lambda to assume execution permissions.



## Section 3 — Lambda Function

```hcl
resource "aws_lambda_function" "processor" {
  function_name = "file-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"

  filename         = "../lambda/function.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda/function.zip")

  environment {
    variables = {
      QUEUE_URL = aws_sqs_queue.queue.id
      DLQ_URL   = aws_sqs_queue.dlq.id
    }
  }
}
```

This defines the Lambda function and injects environment variables for SQS routing.



## Section 4 — S3 Bucket & Trigger

```hcl
resource "aws_s3_bucket" "upload-bucket" {
  bucket = "module4-file-upload-bucket"
}
```

The S3 bucket stores uploaded JSON files.

### Event Notification

```hcl
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.upload-bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}
```

This triggers Lambda whenever a `.json` file is uploaded.



## Section 5 — SQS Queues

```hcl
resource "aws_sqs_queue" "queue" {
  name = "file-queue"
}

resource "aws_sqs_queue" "dlq" {
  name = "file-dlq"
}
```

Two queues are used:

- `file-queue` → valid messages  
- `file-dlq` → invalid messages  



## Section 6 — Lambda Permission

```hcl
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.upload-bucket.arn
}
```

This allows S3 to trigger the Lambda function.



# 5. Test Files

Two sample files are used to test the pipeline:

- `valid.json` → contains required fields (`id`, `name`)
- `invalid.json` → missing required fields

These are uploaded to trigger different routing paths.

# 6. Running the Pipeline

## Start infrastructure

```bash
docker compose up
```

## Deploy Terraform

```bash
terraform apply
```

## Upload test file

```bash
curl -X PUT \
  --data-binary @valid.json \
  http://localhost:4566/module4-file-upload-bucket/valid.json
```

This triggers the full pipeline execution.

# 7. Issues Faced and Fixes

## Issue 1 — LocalStack version mismatch (3.0.2)

LocalStack latest introduced breaking changes in service initialization, causing Terraform resources to fail during provisioning.

**Fix:**  
Pinned LocalStack to a stable compatible version and ensured services (S3, Lambda, SQS) were explicitly enabled in Docker Compose.


## Issue 2 — Lambda runtime image pull failure (Python 3.11)

When deploying the Lambda function, LocalStack attempted to resolve the Python 3.11 Lambda runtime by pulling a corresponding runtime image. Since LocalStack does not automatically have access to AWS-managed Lambda runtime images, it failed with an image pull error.

This happened because the Lambda was defined with:

```hcl
runtime = "python3.11"
```

and LocalStack tried to emulate the AWS Lambda execution environment using a container-based runtime.

**Fix:**  
I resolved this by ensuring the required Python Lambda runtime image was available locally and properly configured for LocalStack to use. This prevented LocalStack from trying to fetch the runtime image from AWS ECR.

## Issue 3 — S3 upload CLI mismatch

The AWS CLI `s3 cp` command did not work reliably with LocalStack due to version and endpoint inconsistencies.

**Fix:**  
Replaced CLI upload with `curl` PUT requests to directly upload objects into the S3 endpoint.


