


declare AWS_ECR_REPO_NAME=quetzal-cognito-api
declare AWS_LAMBDA_FUNCTION_NAME=quetzal-cognito-api

declare DOCKER_IMAGE="public.ecr.aws/lambda/python:3.11"

# Prompt user for a tag
last_tag=$(aws ecr describe-images --repository-name $AWS_ECR_REPO_NAME \
    --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]')

echo "Enter a docker TAG (last: $last_tag)":
read TAG

LOCAL_IMAGE_ID=$(docker images -q $DOCKER_IMAGE)

if [ -z "$LOCAL_IMAGE_ID" ]; then
  echo "Image not found locally. Pulling the latest version."
  docker pull $DOCKER_IMAGE
else
  echo "Local image found. Using the cached version."
fi



# Build docker image
docker build -t $AWS_ECR_REPO_NAME:$TAG .

# Connect to AWS ECR
aws_account=$(aws sts get-caller-identity | jq '.Account' | sed 's/"//g')
aws_region=$(aws configure get region)

aws ecr get-login-password --region $aws_region | docker login --username AWS --password-stdin \
  $aws_account.dkr.ecr.$aws_region.amazonaws.com

#Tag docker
docker tag $AWS_ECR_REPO_NAME:$TAG $aws_account.dkr.ecr.$aws_region.amazonaws.com/$AWS_ECR_REPO_NAME:$TAG

#Push docker to aws
docker push $aws_account.dkr.ecr.$aws_region.amazonaws.com/$AWS_ECR_REPO_NAME:$TAG

#update Lambda
aws lambda update-function-code --region $aws_region --function-name  $AWS_LAMBDA_FUNCTION_NAME \
    --image-uri $aws_account.dkr.ecr.$aws_region.amazonaws.com/$AWS_LAMBDA_FUNCTION_NAME:$TAG > /dev/null