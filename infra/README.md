# INFRA (TERRAFORM)

This repo have the infrastructre for
 * Quetzal-osm-api
 * Quetzal-gtfs-api
 * Quetzal-matrixroadcaster-api
 * Quetzal-cognito-api

 1 **Unlock env.tfvars**

```bash
./config-secret
```
This file contain this information.

    aws_region      = ""
    app_client_id   = ""
    user_pool_id    = ""

2 **plan**

```bash
 terraform plan -var-file="environments/env.tfvars"
```

3 **apply**

```bash
 terraform apply -var-file="environments/env.tfvars"
```

## issues
Lambda function (and ECR) should be updated with the provided script.
if not. Terraform could think that the state changed as the lambda image may not the the latest.