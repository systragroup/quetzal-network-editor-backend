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

docker build --build-arg QUETZAL_MODEL_NAME=%MODEL_FOLDER% ^
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

REM Get existing environment variables
for /f "delims=" %%i in ('aws lambda get-function-configuration --function-name "%AWS_LAMBDA_FUNCTION_NAME%" --query "Environment.Variables" --output json') do set existing_env=%%i

REM Fallback to empty JSON object if null
if "%existing_env%"=="null" set existing_env={}

REM Update IMAGE_TAG using PowerShell
for /f "delims=" %%j in ('powershell -Command ^
  "$env = '%existing_env%'; ^
   $tag = '%TAG%'; ^
   $json = $env | ConvertFrom-Json; ^
   $json.IMAGE_TAG = $tag; ^
   $json | ConvertTo-Json -Compress"') do set updated_env=%%j

REM Build the full payload and call update
powershell -Command ^
  "$fn = '%AWS_LAMBDA_FUNCTION_NAME%'; ^
   $vars = '%updated_env%' | ConvertFrom-Json; ^
   $payload = @{FunctionName=$fn; Environment=@{Variables=$vars}} | ConvertTo-Json -Compress; ^
   aws lambda update-function-configuration --cli-input-json $payload | Out-Null"

echo "success"

endlocal
