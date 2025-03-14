# Quetzal network editor Backend.

This repo host all the infrastructure and scripts for:
 * quetzal models
 * Cognito FastApi
 * Stepfunction Auth
 * microservices


# INFRA (base)
 * Quetzal-osm-api
 * Quetzal-gtfs-api
 * Quetzal-matrixroadcaster-api
 * Quetzal-mapmatching-api
 * Quetzal-cognito-api
 * Quetzal-transit-api

 TODO:
 * quetzal-stepfunction-auth (used in quetzal model step function definition for authorization step.)
 * Api gateway

# INFRA (models)
 * Every models infrastrucure.

# Docker
 * scripts to deploy a Quetzal model
 * scripts to update a Quetzal Model
 * template files for the Quetzal model Configuration


 # Services

 ## Mapmatching
 
 to deploy mapmatching. use the update-lambda script in docker/script
 
 ```sh
 /update-lambda.sh quetzal-network-editor-backend/services/MapMatching
 ```
 update Step-function
 ```sh
  python update-function-config.py quetzal-network-editor-backend/services/MapMatching
 ```

## Transit 
to deploy Transit-api. use the update-lambda script in docker/script

```sh
 /update-lambda.sh quetzal_transit
 ```
 update Step-function
 ```sh
 python update-function-config.py quetzal_transit
```