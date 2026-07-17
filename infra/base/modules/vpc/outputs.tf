output "security_group_id" {
  value = aws_security_group.ecs.id
}



output "subnet" {
  value = module.vpc.public_subnets[0]
}

