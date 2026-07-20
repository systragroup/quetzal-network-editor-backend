
# 1) create an IAM role for exec
resource "aws_iam_role" "ecs_execution_role" {
  name               = "ecs-${var.function_name}-exec-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# attach ecs execution policy
resource "aws_iam_role_policy_attachment" "ecs_exec_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# create actual code permission
resource "aws_iam_role" "ecs_task_role" {
  name               = "ecs-${var.function_name}-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

#  create inline policy to access the s3 Bucket
resource "aws_iam_role_policy" "s3_policy" {
  name   = "S3PutGetObject_${var.function_name}"
  role   = aws_iam_role.ecs_task_role.name
  policy = data.aws_iam_policy_document.s3_policy.json
}

# 2) create Log Group for cloud watch
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/aws/ecs/${var.function_name}"
  retention_in_days = 14
  tags              = var.tags
}


resource "aws_ecs_cluster" "main" {
  name = var.function_name
  tags = var.tags
}


resource "aws_ecs_task_definition" "model" {
  family                   = "${var.function_name}-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  tags                     = var.tags
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  cpu    = var.cpu_units
  memory = var.memory_size
  ephemeral_storage {
    size_in_gib = var.ephemeral_storage
  }



  container_definitions = jsonencode([
    {
      name  = "${var.function_name}"
      image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.region}.amazonaws.com/${var.ecr_repo_name}:${data.aws_ecr_image.latest.image_tags[0]}"

      essential = true

      environment = [
        {
          name  = "BUCKET_NAME"
          value = var.bucket_name
        },
        {
          name  = "TIME_LIMIT"
          value = tostring(var.time_limit)
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "${aws_cloudwatch_log_group.ecs.name}"
          awslogs-region        = "${data.aws_region.current.region}"
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  # lifecycle {
  #   ignore_changes = [
  #     container_definitions
  #   ]
  # }
}

