

variable "admin_role_name" {
  description = "admin role Name only create one time and policies from each workspace added."
  type        = string
  default     = "Cognito_quetzal_pool_admin"
}

variable "cognito_identity_pool_id" {
  description = "cognito_identity_pool_id for the policies"
  type        = string
}
