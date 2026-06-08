# 1) create an IAM role for github CD with Trusted Entities
resource "aws_iam_role" "iam_for_cd" {
  name               = var.role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# 2) create policy to push on ECR
resource "aws_iam_policy" "ecr_push" {
  name        = "${var.role_name}-ecr-push"
  description = "IAM policy to access a model S3 bucket"
  policy      = data.aws_iam_policy_document.ecr_push.json
}

# 3) attach s3 policy to the role
resource "aws_iam_role_policy_attachment" "attach_ecr_push" {
  role       = aws_iam_role.iam_for_cd.name
  policy_arn = aws_iam_policy.ecr_push.arn
}
