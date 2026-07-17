variable "aws_region" {
  description = "set in env.tfvars. Deployment region (e.g.: ca-central-1)"
  type        = string
  default     = "ca-central-1"
}

variable "tags" {
  description = "Tags"
  type        = map(any)
  default     = { "cost:project" = "quetzal" }
}
