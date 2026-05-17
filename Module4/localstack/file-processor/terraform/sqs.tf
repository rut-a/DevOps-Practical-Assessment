resource "aws_sqs_queue" "queue" {
  name = "file-queue"
}

resource "aws_sqs_queue" "dlq" {
  name = "file-dlq"
}