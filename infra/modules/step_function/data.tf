# to get lambda function ARN
data "aws_lambda_function" "lambda" {
  function_name = var.lambda_function_name
}

# Role trusted policy
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}


# Lambda invoke policy
data "aws_iam_policy_document" "sfn_lambda_policy" {
  version = "2012-10-17"
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = ["${data.aws_lambda_function.lambda.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = ["${data.aws_lambda_function.lambda.arn}"]
  }
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = ["arn:aws:lambda:ca-central-1:142023388927:function:quetzal-api-auth:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = ["arn:aws:lambda:ca-central-1:142023388927:function:quetzal-api-auth"]
  }
}
# with ECS policy
# # Lambda invoke policy
# data "aws_iam_policy_document" "sfn_lambda_policy" {
#   version = "2012-10-17"
#   statement {
#     effect    = "Allow"
#     actions   = ["lambda:InvokeFunction"]
#     resources = ["${data.aws_lambda_function.lambda.arn}:*"]
#   }
#   statement {
#     effect = "Allow"
#     actions = [
#       "ecs:RunTask",
#       "ecs:StopTask",
#       "ecs:DescribeTasks"
#     ]
#     resources = ["arn:aws:ecs:ca-central-1:142023388927:task-definition/quetzal-test-task:*"]
#   }
#   statement {
#     effect  = "Allow"
#     actions = ["iam:PassRole"]
#     resources = [
#       "arn:aws:iam::142023388927:role/ecs-quetzal-test-exec-role",
#       "arn:aws:iam::142023388927:role/ecs-quetzal-test-task-role"
#     ]
#   }
#   statement {
#     effect    = "Allow"
#     actions   = ["lambda:InvokeFunction"]
#     resources = ["${data.aws_lambda_function.lambda.arn}"]
#   }
#   statement {
#     effect    = "Allow"
#     actions   = ["lambda:InvokeFunction"]
#     resources = ["arn:aws:lambda:ca-central-1:142023388927:function:quetzal-api-auth:*"]
#   }
#   statement {
#     effect    = "Allow"
#     actions   = ["lambda:InvokeFunction"]
#     resources = ["arn:aws:lambda:ca-central-1:142023388927:function:quetzal-api-auth"]
#   }
#   statement {
#     effect = "Allow"
#     actions = [
#       "events:PutRule",
#       "events:PutTargets",
#       "events:DescribeRule",
#       "events:DeleteRule",
#       "events:RemoveTargets"
#     ]
#     resources = ["*"]
#   }

# }


