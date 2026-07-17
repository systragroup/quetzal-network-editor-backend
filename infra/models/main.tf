terraform {
  backend "s3" {
    bucket  = "quetzal-tf-state"
    key     = "terraform/remote-state/terraform.tfstate"
    region  = "ca-central-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}

# create S3 bucket with CORS policy
module "s3" {
  source      = "./modules/storage"
  bucket_name = var.quetzal_model_name
  tags        = local.quetzal_tags
}

# create ECR instance with a dummy docker image
module "ecr" {
  source    = "../modules/ecr"
  repo_name = var.quetzal_model_name
  tags      = local.quetzal_tags
  os        = var.os
}

# create CloudWatch group, lambda function, IAM role and policy for the lambda function. use dummy image.
module "lambda" {
  count         = var.lambda_memory_size > 0 ? 1 : 0 # ecs or lambda. set in model env variables
  source        = "../modules/lambda"
  depends_on    = [module.ecr]
  function_name = var.quetzal_model_name
  ecr_repo_name = var.quetzal_model_name
  bucket_name   = var.quetzal_model_name
  role_name     = "lambda-${var.quetzal_model_name}-role"
  tags          = local.quetzal_tags
  memory_size   = var.lambda_memory_size
  time_limit    = var.lambda_time_limit
  storage_size  = var.lambda_storage_size
}


# create lambda invoke role (inline policy) and step funtion with  Hello World definition
module "step_function" {
  count                   = var.lambda_memory_size > 0 ? 1 : 0 # ecs or lambda. set in model env variables
  depends_on              = [module.lambda]
  source                  = "../modules/step_function"
  step_function_name      = var.quetzal_model_name
  step_function_role_name = "sfn-${var.quetzal_model_name}-role"
  lambda_function_name    = var.quetzal_model_name
  tags                    = local.quetzal_tags
}



module "ecs" {
  count             = var.ecs_memory_size > 0 ? 1 : 0 # ecs or lambda. set in model env variables
  source            = "../modules/ecs"
  depends_on        = [module.ecr]
  function_name     = var.quetzal_model_name
  ecr_repo_name     = var.quetzal_model_name
  bucket_name       = var.quetzal_model_name
  tags              = local.quetzal_tags
  memory_size       = var.ecs_memory_size
  ephemeral_storage = var.ecs_storage_size
  cpu_units         = var.ecs_cpu_units
}

# create IAM role and policy for Cognito user to access the bucket and other microservices.
module "user_role" {
  source                   = "./modules/user_role"
  cognito_identity_pool_id = var.cognito_identity_pool_id
  user_role_name           = "Cognito_quetzal_pool_${var.quetzal_model_name}"
  s3_policy_name           = "s3_read_put_${var.quetzal_model_name}"
  bucket_name              = var.quetzal_model_name
}

#
# moved block: when count was added on lambda and step_function. it changes the terraform state.
# this make the migration so that terraform apply see no change when we didnt change a old infra lambda.
#
moved {
  from = module.lambda
  to   = module.lambda[0]
}
moved {
  from = module.step_function
  to   = module.step_function[0]
}
moved {
  from = module.ecs
  to   = module.ecs[0]
}
