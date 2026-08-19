
# Role trusted policy
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = ["cognito-identity.amazonaws.com"]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "cognito-identity.amazonaws.com:aud"
      values   = [var.cognito_identity_pool_id]
    }

    condition {
      test     = "ForAnyValue:StringLike"
      variable = "cognito-identity.amazonaws.com:amr"
      values   = ["authenticated"]
    }
  }
}





# policy to read and write on the s3 bucket
data "aws_iam_policy_document" "admin_s3_policy" {
  version = "2012-10-17"
  statement {
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::quetzal-*"]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = ["arn:aws:s3:::quetzal-*/*"]
  }
  statement {
    effect  = "Deny"
    actions = ["*"]
    resources = [
      "arn:aws:s3:::quetzal-tf-state",
      "arn:aws:s3:::quetzal-tf-state/*"
    ]
  }

}




