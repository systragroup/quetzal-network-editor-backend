# 1) create an IAM role for auth user with Trusted Entities
resource "aws_iam_role" "admin_role" {
  name               = var.admin_role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# 2) create S3 policy for the bucket
resource "aws_iam_policy" "admin_s3_policy" {
  name        = "s3_read_put_quetzal_admin"
  description = "IAM policy to access all S3 bucket starting with quetzal-"
  policy      = data.aws_iam_policy_document.admin_s3_policy.json
}

# 3) attach s3 policy to the role
resource "aws_iam_role_policy_attachment" "admin_s3_policy" {
  role       = aws_iam_role.admin_role.name
  policy_arn = aws_iam_policy.admin_s3_policy.arn
}
