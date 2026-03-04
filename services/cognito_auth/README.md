

```bash
pyenv local 3.12
```

```bash
poetry install
```

Then. to run locally
```bash
poetry run uvicorn main:app --reload
```
or
```sh
./start.sh
```

# to deploy

change the variable in update-lambda.sh for dev or prod (quetzal-cognito-api or quetzal-cognito-api-dev)


```bash
 ./update-lambda.sh 
 ```