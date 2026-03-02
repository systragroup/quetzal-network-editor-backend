# this script update lambda with an already pushed docker image on ECR

declare QUETZAL_ROOT=../../..

if [ $# -lt 1 ]
then
  echo "$0 requires 1 argument <model folder>"
  exit -1;
fi

declare MODEL_FOLDER=$1 && shift
declare TAG=$1 && shift

# Change working directory
cd $QUETZAL_ROOT

# Load model .env
#AWS_ECR_REPO_NAME
#AWS_LAMBDA_FUNCTION_NAME 
source $MODEL_FOLDER/.env 

# Connect to AWS ECR
aws_account=$(aws sts get-caller-identity | jq '.Account' | sed 's/"//g')
aws_region=$(aws configure get region)

aws ecr get-login-password --region $aws_region | docker login --username AWS --password-stdin \
  $aws_account.dkr.ecr.$aws_region.amazonaws.com

# get current lambda image tag
current_image=$(aws lambda get-function \
  --function-name "$AWS_LAMBDA_FUNCTION_NAME" \
  --query 'Code.ImageUri' \
  --output text)

current_tag="${current_image##*:}" #keep only the tag at the end


# list tags and prompt user for a tag
# Prompt user for a tag
tags_list=$(aws ecr describe-images \
    --repository-name $AWS_ECR_REPO_NAME \
    --query 'sort_by(imageDetails,& imagePushedAt)[].imageTags[]')

last_tag=$(aws ecr describe-images \
    --repository-name $AWS_ECR_REPO_NAME \
    --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]'  \
    --output text)

echo "this will update : $AWS_ECR_REPO_NAME"
echo "$tags_list"
echo "Select a TAG (current: $current_tag, last: $last_tag)":
read TAG

if [ "$TAG" = "$current_tag" ]; then
    echo "nothing to update"
    exit -1
fi

# Check if TAG is valid
isValid=false
for t in $all_tags; do
    if [ "$t" = "$TAG" ]; then
        isValid=true
        break
    fi
done

if [ "$isValid" = false ]; then
    echo "invalid tag"
    exit -1
fi


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
echo "after"


aws lambda update-function-configuration \
  --cli-input-json "$(jq -n --arg fn "$AWS_LAMBDA_FUNCTION_NAME" --argjson vars "$updated_env" \
    '{FunctionName: $fn, Environment: {Variables: $vars}}')" > /dev/null

echo "success"


#test