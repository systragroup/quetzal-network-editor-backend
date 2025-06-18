declare QUETZAL_ROOT=../../..

if [ $# -lt 2 ]
then
  echo "$0 requires 2 argument <model folder> <tag>"
  exit -1;
fi

declare MODEL_FOLDER=$1 && shift
declare TAG=$1 && shift

# Change working directory
cd $QUETZAL_ROOT

# Load model .env
source $MODEL_FOLDER/.env

# Build docker image
docker build --build-arg QUETZAL_MODEL_NAME=$MODEL_FOLDER \
  -t $AWS_ECR_REPO_NAME:$TAG \
  -f $MODEL_FOLDER/Dockerfile .

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

echo "updating lambda function ..."

aws lambda wait function-updated --region $aws_region --function-name $AWS_LAMBDA_FUNCTION_NAME

# Update Lamdba configuration to set tag  
# Get current environment variables
existing_env=$(aws lambda get-function-configuration \
  --function-name "$AWS_LAMBDA_FUNCTION_NAME" \
  --query 'Environment.Variables' \
  --output json)

# Fallback to empty object if null
existing_env=${existing_env:-{}}

updated_env=$(echo "$existing_env" | jq -c --arg TAG "$TAG" '. + {IMAGE_TAG: $TAG}')

aws lambda update-function-configuration \
  --cli-input-json "$(jq -n --arg fn "$AWS_LAMBDA_FUNCTION_NAME" --argjson vars "$updated_env" \
    '{FunctionName: $fn, Environment: {Variables: $vars}}')" > /dev/null

echo "success"
