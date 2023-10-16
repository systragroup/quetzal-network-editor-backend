
firt. install dependancies
```bash
pipenv install
```
change the env variable in auth.py and main.py (ex: USER_POOL_ID = 'this_is_a_string')<br>
Then. to run locally
```bash
pipenv run uvicorn main:app --reload
```

to deploy

```bash
 ./update-lambda.sh 
 ```