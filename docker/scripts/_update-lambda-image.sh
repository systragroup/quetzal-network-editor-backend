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

#update Lambda
aws lambda update-function-code --region $aws_region --function-name  $AWS_ECR_REPO_NAME \
    --image-uri $aws_account.dkr.ecr.$aws_region.amazonaws.com/$AWS_ECR_REPO_NAME:$TAG > /dev/null

echo "updating lambda function ..."

aws lambda wait function-updated --region $aws_region --function-name $AWS_ECR_REPO_NAME

echo "updating lambda Tags ..."
echo "success"