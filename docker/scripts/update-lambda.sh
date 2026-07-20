#!/bin/bash

# *******************************************************
# This script build and push docker on AWS ECR
# Update Lambda with new image tag
#*******************************************************

if [ $# -lt 1 ]
then
  echo "$0 requires 1 argument <model folder>"
  exit -1;
fi

declare MODEL_FOLDER=$1 && shift
declare QUETZAL_ROOT=../../..
# Load model .env
source $QUETZAL_ROOT/$MODEL_FOLDER/.env

# Prompt user for a tag
last_tag=$(aws ecr describe-images --repository-name $AWS_ECR_REPO_NAME \
    --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]')
echo "this will update : $AWS_ECR_REPO_NAME"
echo "Enter a docker TAG (last: $last_tag)":
read TAG

./_push-image.sh $MODEL_FOLDER $TAG


./_update-lambda-image.sh $MODEL_FOLDER $TAG







