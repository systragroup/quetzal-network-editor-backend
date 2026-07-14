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
docker tag $ECR_IMAGE
docker push  $ECR_IMAGE

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