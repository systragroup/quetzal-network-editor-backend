variable "function_name" {
  description = "ECS function name"
  type        = string
}
variable "vpc_id" {
  description = "vpc_id"
  type        = string
}


variable "tags" {
  description = "Tags"
  type        = map(any)
  default     = { "cost:project" = "quetzal" }
}
variable "ecr_repo_name" {
  description = "function ECR repo Name"
  type        = string
}
variable "bucket_name" {
  description = "s3 bucket name for env variable"
  type        = string
}
variable "memory_size" {
  description = "fargate function ram in mb"
  default     = 4096
  type        = number
}

variable "time_limit" {
  description = "fargate function time limit in seconds"
  default     = 300
  type        = number
}
variable "cpu_units" {
  description = "fargate cpu units"
  default     = 1024
  type        = number
}

