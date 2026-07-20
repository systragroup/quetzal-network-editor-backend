# VPC
module "vpc" {
  source               = "terraform-aws-modules/vpc/aws"
  name                 = "quetzal-vpc"
  cidr                 = "10.0.0.0/16"
  azs                  = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets      = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets       = ["10.0.101.0/24", "10.0.102.0/24"]
  enable_dns_hostnames = true
  tags                 = var.tags
}


resource "aws_security_group" "ecs" {
  name   = "quetzal-ecs-sg"
  vpc_id = module.vpc.vpc_id
  tags   = var.tags

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
