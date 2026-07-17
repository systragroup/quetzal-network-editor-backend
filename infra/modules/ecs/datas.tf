
data "aws_caller_identity" "current" {}
data "aws_region" "current" {} # data.aws_region.current.name
data "aws_ecr_image" "latest" {
  repository_name = var.ecr_repo_name
  most_recent     = true
}



data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# policy to read and write on the s3 bucket
data "aws_iam_policy_document" "s3_policy" {
  version = "2012-10-17"
  statement {
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::${var.bucket_name}"]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = ["arn:aws:s3:::${var.bucket_name}/*"]
  }
  statement {
    effect = "Deny"
    actions = [
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = ["arn:aws:s3:::${var.bucket_name}/base/*"]
  }

}


