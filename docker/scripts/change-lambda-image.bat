@echo off
setlocal enabledelayedexpansion

set "QUETZAL_ROOT=..\..\.."


if "%~1"=="" (
  echo "%0 requires 1 argument <model folder>"
  exit /b -1
)
set "MODEL_FOLDER=%~1"
shift


set ENV_FILE=%QUETZAL_ROOT%\%MODEL_FOLDER%\.env
:: Load model .env
:: Loop through the lines in the .env file and set environment variables
for /f "delims=" %%a in (%ENV_FILE%) do (
    set %%a
)
echo %AWS_ECR_REPO_NAME%

:: Prompt user for a tag
for /f %%i in ('aws ecr describe-images --repository-name %AWS_ECR_REPO_NAME% ^
    --query "sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]"') do set "last_tag=%%i"

for /f "usebackq tokens=*" %%i in (`aws ecr describe-images --repository-name %AWS_ECR_REPO_NAME% ^
    --query "imageDetails[].imageTags[]" --output text`) do set "all_tags=%%i"

echo Available tags: %all_tags%
set /p TAG="Enter a docker TAG (last: !last_tag!): "


REM Connect to ECR
FOR /F "tokens=* USEBACKQ" %%F IN (`aws sts get-caller-identity --query "Account" --output text`) DO (
SET aws_account=%%F
)
FOR /F "tokens=* USEBACKQ" %%F IN (`aws configure get region`) DO (
SET aws_region=%%F
)

REM update Lambda
aws lambda update-function-code --region %aws_region% --function-name  %AWS_LAMBDA_FUNCTION_NAME% ^
    --image-uri %aws_account%.dkr.ecr.%aws_region%.amazonaws.com/%AWS_LAMBDA_FUNCTION_NAME%:%TAG%

echo "updating lambda function ..."

aws lambda wait function-updated --region %aws_region% --function-name  %AWS_LAMBDA_FUNCTION_NAME%


REM 1) get current env variables
aws lambda get-function-configuration ^
    --function-name "%AWS_LAMBDA_FUNCTION_NAME%" ^
    --query "Environment.Variables" ^
    --output json > _env.json


REM 2) update env with new tag
powershell -NoProfile -Command ^
    "$env = Get-Content '_env.json' | ConvertFrom-Json; if ($null -eq $env) { $env = @{} }; $env.IMAGE_TAG = '%TAG%'; @{Variables=$env} | ConvertTo-Json -Compress | Set-Content '_env.json'"

REM  3) update lambda with new tags
aws lambda update-function-configuration ^
    --function-name "%AWS_LAMBDA_FUNCTION_NAME%" ^
    --environment file://_env.json
    
del _env.json

echo success 

endlocal
