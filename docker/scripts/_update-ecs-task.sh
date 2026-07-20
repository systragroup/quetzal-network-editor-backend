#!/bin/bash

# *******************************************************
# This script update ECS task definition with new docker image.
#*******************************************************

if [ $# -lt 2 ]
then
  echo "$0 requires 2 argument <model folder> <tag>"
  exit -1;
fi

declare MODEL_FOLDER=$1 && shift
declare TAG=$1 && shift
declare QUETZAL_ROOT=../../..
# Load model .env
source $QUETZAL_ROOT/$MODEL_FOLDER/.env

# Connect to AWS ECR
aws_account=$(aws sts get-caller-identity | jq '.Account' | sed 's/"//g')
aws_region=$(aws configure get region)


ECR_IMAGE="$aws_account.dkr.ecr.$aws_region.amazonaws.com/$AWS_ECR_REPO_NAME:$TAG"

# get task definition. update it and uupload it
task_definition=$(aws ecs describe-task-definition \
  --task-definition $AWS_ECR_REPO_NAME-task \
  --query taskDefinition \
  --output json)

# change image
# delete stuff like task definition as a new one will  be created
task_definition=$(jq -c --arg IMAGE "$ECR_IMAGE" '.containerDefinitions[0].image = $IMAGE  
       | del(
        .taskDefinitionArn,
        .revision,
        .status,
        .requiresAttributes,
        .compatibilities,
        .registeredAt,
        .registeredBy
      )' <<< "$task_definition")

new_task_definition=$(aws ecs register-task-definition \
  --cli-input-json "$task_definition" \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)


echo "New task definition: $new_task_definition"
echo "success"