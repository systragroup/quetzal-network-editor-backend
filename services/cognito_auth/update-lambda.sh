declare AWS_ECR_REPO_NAME=quetzal-cognito-api
declare AWS_LAMBDA_FUNCTION_NAME=quetzal-cognito-api

last_tag=$(aws ecr describe-images --repository-name $AWS_ECR_REPO_NAME \
    --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]')
echo "last tag: $last_tag":
# get version in pyproject.toml for the tag
TAG=$(grep '^version' pyproject.toml | head -1 | sed 's/version *= *"\(.*\)"/\1/')
# Ask user to continue
read -p "Do you want to deploy $TAG (from pyproject.toml) on $AWS_ECR_REPO_NAME? (y/n): " CONFIRM
CONFIRM=$(echo "$CONFIRM" | tr '[:upper:]' '[:lower:]')  # convert to lowercase

if [[ "$CONFIRM" != "y" && "$CONFIRM" != "yes" ]]; then
    echo "Deployment cancelled."
    exit 1
fi


# Build docker image
docker build --provenance=false -t $AWS_ECR_REPO_NAME:$TAG .

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