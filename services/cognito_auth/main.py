import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
from models import RunPayload, Status, DisplayStepsDict, Infra
from auth import auth, get_user_policies, get_available_buckets
from ecs import (
	run_ecs,
	get_ecs_status,
	stop_ecs_task,
	get_running_ecs_task,
	get_image_tag,
	get_ecs_steps,
	list_tasks_revisions,
)
from stepfunctions import (
	run_stepfunctions,
	stop_stepfunctions,
	get_lambda_image_tag,
	get_running_stepfunctions,
	get_stepfunctions_steps,
	get_stepfunctions_status,
)
from step_status import StepStatusController, StepStatus
from typing import Optional, Annotated
import toml


from middlewares.exception import ExceptionHandlerMiddleware


class User(BaseModel):
	username: str
	given_name: Optional[str] = None
	family_name: Optional[str] = None
	email: Optional[str] = None
	password: str


class Username(BaseModel):
	username: str


USER_POOL_ID = os.environ['USER_POOL_ID']

client = boto3.client('cognito-idp')
pyproject = toml.load('pyproject.toml')
VERSION = pyproject['tool']['poetry']['version']


app = FastAPI()
# this is for AXIOS in vueJS (local dev)
origins = [
	'http://localhost:8081',
	'https://localhost:8081',
	'https://systragroup.github.io/quetzal-network-editor-dev/',
	'https://systragroup.github.io',
	'https://systragroup.github.io/quetzal-network-editor/',
]

app.add_middleware(
	CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*']
)

app.add_middleware(ExceptionHandlerMiddleware)


@app.get('/')
def read_root():
	return {'Hello': 'Quenedi Cognito API'}


@app.get('/version')
def version():
	return {'version': VERSION}


@app.get('/buckets/')
async def get_buckets(Authorization: Annotated[str | None, Header()] = None):
	claims = auth(Authorization)
	policies = get_user_policies(claims)
	buckets = get_available_buckets(policies)
	buckets.sort()
	return buckets


def get_user_groups(claims) -> list[str]:
	# return the list of available user_groups for a given user
	# this is Bucket based. so you only see groups with the name == bucket name
	user_group = claims['cognito:groups'][0]
	_all_groups = [group['GroupName'] for group in client.list_groups(UserPoolId=USER_POOL_ID)['Groups']]
	if user_group == 'admin':
		return _all_groups
	else:
		# list policies to find all available buckets
		policies = get_user_policies(claims)
		buckets = get_available_buckets(policies)
		_all_groups = [group['GroupName'] for group in client.list_groups(UserPoolId=USER_POOL_ID)['Groups']]
		available_groups = [name for name in _all_groups if name in buckets]
		# insert actual user group as first in the list
		available_groups = [name for name in available_groups if name != user_group]
		available_groups = [user_group, *available_groups]
		return available_groups


@app.get('/listGroups/')
async def list_groups(Authorization: Annotated[str | None, Header()] = None):
	claims = auth(Authorization)
	groups = get_user_groups(claims)
	return groups


@app.get('/listUser/{group}/')
async def list_users(group: str, Authorization: Annotated[str | None, Header()] = None):
	claims = auth(Authorization)
	if group not in get_user_groups(claims):
		raise HTTPException(status_code=401, detail='not allowed')

	# Can be paginated with NextToken
	response = client.list_users_in_group(UserPoolId=USER_POOL_ID, GroupName=group)
	temp_users = response['Users']
	while 'NextToken' in response.keys():
		nextToken = response['NextToken']
		response = client.list_users_in_group(UserPoolId=USER_POOL_ID, GroupName=group, NextToken=nextToken)
		temp_users.extend(response['Users'])

	users = []
	for user in temp_users:
		attrs_dict = {attr['Name']: attr['Value'] for attr in user['Attributes']}
		user.update(attrs_dict)
		user.pop('Attributes', None)
		users.append(user)
	users.sort(key=lambda x: x['Username'])
	return users


@app.post('/setUserPassword/')
async def set_password(payload: User, Authorization: Annotated[str | None, Header()] = None):
	claims = auth(Authorization)

	user_group = claims['cognito:groups'][0]
	if user_group not in get_user_groups(claims):
		raise HTTPException(status_code=401, detail='not allowed')

	try:
		response = client.admin_set_user_password(
			UserPoolId=USER_POOL_ID, Username=payload.username, Password=payload.password, Permanent=False
		)
	except Exception as err:
		raise HTTPException(status_code=400, detail=str(err))

	return response


@app.post('/createUser/{group}/')
async def create_user(group: str, payload: User, Authorization: Annotated[str | None, Header()] = None):
	claims = auth(Authorization)
	user_group = claims['cognito:groups'][0]
	if user_group not in get_user_groups(claims):
		raise HTTPException(status_code=401, detail='not allowed')

	try:
		response = client.admin_create_user(
			UserPoolId=USER_POOL_ID,
			Username=payload.username,
			UserAttributes=[
				{'Name': 'email', 'Value': payload.email},
				{'Name': 'email_verified', 'Value': 'true'},
				{'Name': 'given_name', 'Value': payload.given_name},
				{'Name': 'family_name', 'Value': payload.family_name},
			],
			TemporaryPassword=payload.password,
		)
		try:
			## add user to group
			response = client.admin_add_user_to_group(
				UserPoolId=USER_POOL_ID, Username=payload.username, GroupName=group
			)
		except Exception as err:
			raise HTTPException(status_code=400, detail=str(err))

	except Exception as err:
		raise HTTPException(status_code=400, detail=str(err))
	return response


@app.post('/deleteUser/')
async def delete_user(payload: Username, Authorization: Annotated[str | None, Header()] = None):
	claims = auth(Authorization)
	user_group = claims['cognito:groups'][0]
	user_name = claims['cognito:username']
	if user_group not in get_user_groups(claims):
		raise HTTPException(status_code=401, detail='not allowed')
	if payload.username == user_name:
		raise HTTPException(status_code=403, detail='cannot delete yourself')
	try:
		response = client.admin_delete_user(UserPoolId=USER_POOL_ID, Username=payload.username)
	except Exception as err:
		raise HTTPException(status_code=400, detail=str(err))

	return response


#
# Quetzal Api run
#


def on_ecs(infra: Infra) -> bool:
	return infra.lower() == 'ecs'


@app.get('/run/{function_name}/infra', response_model=Infra)
def get_infra(function_name: str):
	ecs_tasks = list_tasks_revisions(function_name)
	if len(ecs_tasks) > 0:
		return 'ecs'
	else:
		return 'lambda'


# get steps
@app.get('/{infra}/run/{function_name}/steps', response_model=DisplayStepsDict)
def get_steps_definition(infra: Infra, function_name: str):
	print(infra)
	if on_ecs(infra):
		res = get_ecs_steps(function_name)
		return res
	else:
		res = get_stepfunctions_steps(function_name=function_name)
		return res


# start
@app.post('/{infra}/run', response_model=str)
def run_task(infra: Infra, payload: RunPayload, Authorization: Annotated[str | None, Header()] = None):
	auth(Authorization)
	if on_ecs(infra):
		job_id = run_ecs(
			function_name=payload.function_name,
			scenario_path=payload.scenario_path,
			launcher_arg=payload.launcher_arg,
			steps=payload.steps,
			variants=payload.variants,
			metadata=payload.metadata,
		)
	else:
		job_id = run_stepfunctions(
			function_name=payload.function_name,
			scenario_path=payload.scenario_path,
			launcher_arg=payload.launcher_arg,
			variants=payload.variants,
			metadata=payload.metadata,
		)
		# init step_status to new run
	step_status = StepStatusController(
		bucket_name=payload.function_name, scenario=payload.scenario_path, metadata=payload.metadata
	)
	step_status.put_status(StepStatus())
	return job_id


# stop
@app.post('/{infra}/run/{function_name}/job_id/{job_id:path}/stop', response_model=bool)
def stop_task(infra: Infra, function_name: str, job_id: str, Authorization: Annotated[str | None, Header()] = None):
	auth(Authorization)
	if on_ecs(infra):
		return stop_ecs_task(function_name=function_name, job_id=job_id)
	else:
		return stop_stepfunctions(function_name=function_name, job_id=job_id)


# get status
@app.get('/{infra}/run/{function_name}/job_id/{job_id:path}/scenario/{scenario}', response_model=Status)
def get_status(infra: Infra, function_name: str, job_id: str, scenario: str):
	if on_ecs(infra):
		ecs_status = get_ecs_status(function_name=function_name, job_id=job_id)
		step_status = StepStatusController(bucket_name=function_name, scenario=scenario).get_status()
		return Status(job_id=job_id, status=ecs_status, step_status=step_status)
	else:
		status = get_stepfunctions_status(job_id)
		return status


# get tasks aready running
@app.get('/{infra}/run/{function_name}/scenario/{scenario}/', response_model=str)
def get_running_task_id(
	infra: Infra, function_name: str, scenario: str, Authorization: Annotated[str | None, Header()] = None
):
	auth(Authorization)
	if on_ecs(infra):
		return get_running_ecs_task(function_name=function_name, scenario=scenario)
	else:
		return get_running_stepfunctions(function_name=function_name, scenario=scenario)


@app.get('/{infra}/run/{function_name}/tag')
def get_ecs_task_image_tag(infra: Infra, function_name: str, Authorization: Annotated[str | None, Header()] = None):
	auth(Authorization)
	if on_ecs(infra):
		return get_image_tag(function_name)
	else:
		return get_lambda_image_tag(function_name)


handler = Mangum(app=app)
