resource "aws_lambda_function" "processor" {
  function_name = "file-processor"
  role = aws_iam_role.lambda_role.arn
  handler = "handler.lambda_handler"
  runtime = "python3.11"
  architectures = ["x86_64"]

  filename = "../lambda/function.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda/function.zip")

  environment {
    variables = {
      QUEUE_URL = aws_sqs_queue.queue.id
      DLQ_URL   = aws_sqs_queue.dlq.id
    }
  }
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id = "AllowS3Invoke"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal = "s3.amazonaws.com"
  source_arn = aws_s3_bucket.upload-bucket.arn
}