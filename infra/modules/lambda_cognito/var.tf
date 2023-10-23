variable "function_name" {
  description = "Lambda function name"
  type        = string
}
variable "role_name" {
  description = "Lambda function role  name"
  type        = string
}
variable "tags" {
    description = "Tags"
    type        = map
    default     = {"cost:project"="quetzal"}
}
variable "ecr_repo_name" {
  description = "Lambda function ECR repo Name"
  type        = string
}
variable "region" {
  description = "aws region"
  type        = string
}
variable "app_client_id" {
  description = "aws cognito pool app client id"
  type        = string
}
variable "user_pool_id" {
  description = "aws user pool id"
  type        = string
}
variable "memory_size" {
  description = "Lambda function ram in mb"
  default     = 4016
  type        = number
}

variable "time_limit" {
  description = "Lambda function time limit in seconds"
  default     = 300
  type        = number
}
variable "storage_size" {
  description = "Lambda function ephemeral storage size in mb"
  default     = 4016
  type        = number
}
