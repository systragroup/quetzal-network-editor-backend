@echo off
setlocal enabledelayedexpansion

set "QUETZAL_ROOT=..\..\.."

IF "%~2"=="" (
  echo "%0 requires at least 2 arguments <model folder> <tag>"
  exit /b 1
)

SET MODEL_FOLDER=%1
SET TAG=%2

cd %QUETZAL_ROOT%

FOR /F "tokens=*" %%i in ('type "%MODEL_FOLDER%\.env"') do (SET "%%i")

docker build --provenance=false --build-arg QUETZAL_MODEL_NAME=%MODEL_FOLDER% ^
  -t %AWS_ECR_REPO_NAME%:%TAG% ^
  -f %MODEL_FOLDER%/Dockerfile .

REM Connect to ECR
FOR /F "tokens=* USEBACKQ" %%F IN (`aws sts get-caller-identity --query "Account" --output text`) DO (
SET aws_account=%%F
)
FOR /F "tokens=* USEBACKQ" %%F IN (`aws configure get region`) DO (
SET aws_region=%%F
)

aws ecr get-login-password --region %aws_region%  | docker login --username AWS --password-stdin %aws_account%.dkr.ecr.%aws_region%.amazonaws.com


REM Tag docker
docker tag %AWS_ECR_REPO_NAME%:%TAG% %aws_account%.dkr.ecr.%aws_region%.amazonaws.com/%AWS_ECR_REPO_NAME%:%TAG%

REM Push docket to aws
docker push %aws_account%.dkr.ecr.%aws_region%.amazonaws.com/%AWS_ECR_REPO_NAME%:%TAG%


REM update Lambda
aws lambda update-function-code --region %aws_region% --function-name  %AWS_LAMBDA_FUNCTION_NAME% ^
    --image-uri %aws_account%.dkr.ecr.%aws_region%.amazonaws.com/%AWS_LAMBDA_FUNCTION_NAME%:%TAG%

echo "updating lambda function ..."

aws lambda wait function-updated --region %aws_region% --function-name  %AWS_LAMBDA_FUNCTION_NAME%


echo "updating lambda Tags ..."

REM 1) get current env variables and write a temporary json file (_env.json)
aws lambda get-function-configuration ^
    --function-name "%AWS_LAMBDA_FUNCTION_NAME%" ^
    --query "Environment.Variables" ^
    --output json > _env.json

REM 2) update env with new tag. and rename {Variable:{..}} for the was command to work
powershell -NoProfile -Command ^
    "$env = Get-Content '_env.json' | ConvertFrom-Json; if ($null -eq $env) { $env = @{} }; $env.IMAGE_TAG = '%TAG%'; @{Variables=$env} | ConvertTo-Json -Compress | Set-Content '_env.json'"

REM  3) update lambda with new tags
aws lambda update-function-configuration ^
    --function-name "%AWS_LAMBDA_FUNCTION_NAME%" ^
    --environment file://_env.json
    
REM delete the temp json tile
del _env.json 


echo "success"

endlocal
