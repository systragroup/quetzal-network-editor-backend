terraform {
  backend "s3" {
    bucket = "quetzal-tf-state"
    key = "infra/remote-state/terraform.tfstate"
    region = "ca-central-1"
    encrypt = true
  }
}

provider "aws" {
    region = var.aws_region
}


# create S3 bucket with CORS policy
module "s3" {
    source = "./modules/storage"
    bucket_name = var.bucket_name       
    tags = local.general_tags
}
# =========
# GTFS API
# =========

# create ECR isntance with a dummy docker image
module "ecr-gtfs" {
    source = "./modules/ecr"
    repo_name = var.gtfs_api_name
    tags = local.gtfs_api_tags     
}

# create CloudWatch group, lambda function, IAM role and policy for the lambda function. use dummy image.
module "lambda-gtfs" {
    source = "./modules/lambda"
    depends_on = [module.ecr-gtfs]
    function_name = var.gtfs_api_name
    ecr_repo_name = var.gtfs_api_name  
    bucket_name = var.bucket_name
    role_name = "lambda-${var.gtfs_api_name}-role"
    tags = local.gtfs_api_tags
    memory_size = var.gtfs_api_memory_size
    time_limit = var.gtfs_api_time_limit
    storage_size  = var.gtfs_api_storage_size
}

# create lambda invoke role (inline policy) and step funtion with  Hello World definition
module "step_function-gtfs" {
    depends_on = [module.lambda-gtfs]
    source = "./modules/step_function"
    step_function_name = var.gtfs_api_name     
    state_machine_definition = var.gtfs_api_state_machine
    step_function_role_name="sfn-${var.gtfs_api_name}-role"
    lambda_function_name = var.gtfs_api_name
    tags = local.gtfs_api_tags 
}


# =========
# osm API
# =========

# create ECR isntance with a dummy docker image
module "ecr-osm" {
    source = "./modules/ecr"
    repo_name = var.osm_api_name
    tags = local.osm_api_tags     
}

# create CloudWatch group, lambda function, IAM role and policy for the lambda function. use dummy image.
module "lambda-osm" {
    source = "./modules/lambda"
    depends_on = [module.ecr-osm]
    function_name = var.osm_api_name
    ecr_repo_name = var.osm_api_name  
    bucket_name = var.bucket_name
    role_name = "lambda-${var.osm_api_name}-role"
    tags = local.osm_api_tags
    memory_size = var.osm_api_memory_size
    time_limit = var.osm_api_time_limit
    storage_size  = var.osm_api_storage_size
}

# create lambda invoke role (inline policy) and step funtion with  Hello World definition
module "step_function-osm" {
    depends_on = [module.lambda-osm]
    source = "./modules/step_function"
    step_function_name = var.osm_api_name     
    state_machine_definition = var.osm_api_state_machine
    step_function_role_name="sfn-${var.osm_api_name}-role"
    lambda_function_name = var.osm_api_name
    tags = local.osm_api_tags 
}


# =========
# matrixroadcaster API
# =========

# create ECR isntance with a dummy docker image
module "ecr-matrixroadcaster" {
    source = "./modules/ecr"
    repo_name = var.matrixroadcaster_api_name
    tags = local.matrixroadcaster_api_tags     
}

# create CloudWatch group, lambda function, IAM role and policy for the lambda function. use dummy image.
module "lambda-matrixroadcaster" {
    source = "./modules/lambda"
    depends_on = [module.ecr-matrixroadcaster]
    function_name = var.matrixroadcaster_api_name
    ecr_repo_name = var.matrixroadcaster_api_name  
    bucket_name = var.bucket_name
    role_name = "lambda-${var.matrixroadcaster_api_name}-role"
    tags = local.matrixroadcaster_api_tags
    memory_size = var.matrixroadcaster_api_memory_size
    time_limit = var.matrixroadcaster_api_time_limit
    storage_size  = var.matrixroadcaster_api_storage_size
}

# create lambda invoke role (inline policy) and step funtion with  Hello World definition
module "step_function-matrixroadcaster" {
    depends_on = [module.lambda-matrixroadcaster]
    source = "./modules/step_function"
    step_function_name = var.matrixroadcaster_api_name     
    state_machine_definition = var.matrixroadcaster_api_state_machine
    step_function_role_name="sfn-${var.matrixroadcaster_api_name}-role"
    lambda_function_name = var.matrixroadcaster_api_name
    tags = local.matrixroadcaster_api_tags 
}