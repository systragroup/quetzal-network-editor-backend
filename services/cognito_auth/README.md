
firt. install dependancies
```bash
pipenv install
```
export your env variables:
```bash
export USER_POOL_ID=
export APP_CLIENT_ID=
export REGION=ca-central-1
```

Then. to run locally
```bash
pipenv run uvicorn main:app --reload
```

to deploy

```bash
 ./update-lambda.sh 
 ```