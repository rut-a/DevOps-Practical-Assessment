import json
import boto3
import os

s3 = boto3.client("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL"))
sqs = boto3.client("sqs", endpoint_url=os.environ.get("AWS_ENDPOINT_URL"))

QUEUE_URL = os.environ["QUEUE_URL"]
DLQ_URL = os.environ["DLQ_URL"]

def is_valid(payload):
    required_fields = ["id", "name"]
    return all(field in payload for field in required_fields)

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