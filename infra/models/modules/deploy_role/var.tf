variable "role_name" {
  description = "CD role Name"
  type        = string
}
variable "ecr_repo" {
  description = "quetzal_model_name"
  type        = string
}

variable "github_repo" {
  description = "Allowed GitHub repo in org/repo format"
  type        = string
}

variable "gitlab_repo" {
  description = "Allowed GitLab project in group/project format"
  type        = string
}
