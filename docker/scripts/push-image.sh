#!/bin/bash

# *******************************************************
# This script build and push docker to ECR
#***********************************************


if [ $# -lt 2 ]
then
  echo "$0 requires 2 argument <model folder> <tag>"
  exit -1;
fi

declare MODEL_FOLDER=$1 && shift
declare TAG=$1 && shift
declare QUETZAL_ROOT=../../..
# Change working directory
cd $QUETZAL_ROOT

# Load model .env
source $MODEL_FOLDER/.env

# Build docker image  # new docker version create metadata that are not supported by lambda 
docker build  --provenance=false --build-arg QUETZAL_MODEL_NAME=$MODEL_FOLDER \
  -t $AWS_ECR_REPO_NAME:$TAG \
  -f $MODEL_FOLDER/Dockerfile .

# Connect to AWS ECR
aws_account=$(aws sts get-caller-identity | jq '.Account' | sed 's/"//g')
aws_region=$(aws configure get region)

aws ecr get-login-password --region $aws_region | docker login --username AWS --password-stdin \
  $aws_account.dkr.ecr.$aws_region.amazonaws.com

# tag and push the docker
ECR_IMAGE="$aws_account.dkr.ecr.$aws_region.amazonaws.com/$AWS_ECR_REPO_NAME:$TAG"
docker tag $AWS_ECR_REPO_NAME:$TAG  $ECR_IMAGE
docker push  $ECR_IMAGE

echo "$ECR_IMAGE pushed"
