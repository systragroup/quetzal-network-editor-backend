
data "aws_caller_identity" "current" {}
data "aws_region" "current" {} # data.aws_region.current.name
data "aws_ecr_image" "latest" {
  repository_name   = var.ecr_repo_name
  most_recent       = true
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# policy to log on cloudwatch. using the just created log group arn
data "aws_iam_policy_document" "lambda_logging" {
    version = "2012-10-17"
    statement   {
        effect = "Allow"
        actions = ["logs:CreateLogGroup"]
        resources = [
            "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
            ]
    }
    statement {
        effect = "Allow"
        actions = [
            "logs:CreateLogStream",
            "logs:PutLogEvents"
        ]
        resources = [
            "${aws_cloudwatch_log_group.log_group.arn}:*"
        ]
    }
}

# policy to read and write on the s3 bucket
data "aws_iam_policy_document" "iam_policy" {
    version = "2012-10-17"
	statement	{
        effect= "Allow"
        actions= [
            "iam:GetPolicyVersion",
			"iam:GetPolicy",
			"iam:ListAttachedRolePolicies"
        ]
        resources= ["*"]
    }
}


# policy to read and write on the s3 bucket
data "aws_iam_policy_document" "cognito_policy" {
    version = "2012-10-17"
	statement	{
        effect= "Allow"
        actions= [
            "cognito-idp:ForgotPassword",
            "cognito-idp:GlobalSignOut",
            "cognito-idp:ConfirmSignUp",
            "cognito-idp:CreateUserPool",
            "cognito-idp:ForgetDevice",
            "cognito-idp:RevokeToken",
            "cognito-idp:GetUserAttributeVerificationCode",
            "cognito-idp:InitiateAuth",
            "cognito-idp:DeleteUser",
            "cognito-idp:SetUserMFAPreference",
            "cognito-idp:GetUser",
            "cognito-idp:ConfirmForgotPassword",
            "cognito-idp:SetUserSettings",
            "cognito-idp:SignUp",
            "cognito-idp:VerifyUserAttribute",
            "cognito-idp:ListDevices",
            "cognito-idp:AdminSetUserPassword",
            "cognito-idp:ListUserPools",
            "cognito-idp:AssociateSoftwareToken",
            "cognito-idp:VerifySoftwareToken",
            "cognito-idp:GetDevice",
            "cognito-idp:RespondToAuthChallenge",
            "cognito-idp:DeleteUserAttributes",
            "cognito-idp:UpdateUserAttributes",
            "cognito-idp:DescribeUserPoolDomain",
            "cognito-idp:UpdateDeviceStatus",
            "cognito-idp:ChangePassword",
            "cognito-idp:ConfirmDevice",
            "cognito-idp:ResendConfirmationCode"
        ]
        resources= ["*"]
    }
    statement	{
        effect= "Allow"
        actions= ["cognito-idp:*"]
        resources= ["arn:aws:cognito-idp:*:142023388927:userpool/*"]
    }
}