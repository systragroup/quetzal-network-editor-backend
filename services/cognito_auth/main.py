import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from run.models import RunPayload, Status, DisplayStepsDict, Infra, PollPayload, StopPayload
from auth import auth, get_user_policies, get_available_buckets, checkAccessToBucket
from users.cognito import (
	get_user_groups,
	list_group_users,
	set_user_password,
	create_user,
	delete_user_by_username,
)

from run.ecs import (
	run_ecs,
	get_ecs_status,
	stop_ecs_task,
	get_running_ecs_task,
	get_image_tag,
	get_ecs_steps,
	list_tasks_revisions,
	get_ecs_bucket,
)
from run.stepfunctions import (
	run_stepfunctions,
	stop_stepfunctions,
	get_lambda_image_tag,
	get_running_stepfunctions,
	get_stepfunctions_steps,
	get_stepfunctions_status,
	get_lambda_bucket,
)
from run.step_status import StepStatusController, StepStatus
from typing import Optional, Annotated
import toml


from middlewares.exception import ExceptionHandlerMiddleware

type AuthHeader = Annotated[str, Header()]


class User(BaseModel):
	username: str
	given_name: Optional[str] = None
	family_name: Optional[str] = None
	email: Optional[str] = None
	password: str


class Username(BaseModel):
	username: str


pyproject = toml.load('pyproject.toml')
VERSION = pyproject['tool']['poetry']['version']

if os.environ.get('DEV', False):
	origins = [
		'http://localhost:8081',
		'https://localhost:8081',
	]
else:
	origins = [
		'https://systragroup.github.io/quetzal-network-editor-dev/',
		'https://systragroup.github.io',
		'https://systragroup.github.io/quetzal-network-editor/',
	]

app = FastAPI()

app.add_middleware(
	CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*']
)

app.add_middleware(ExceptionHandlerMiddleware)


@app.get('/')
def read_root():
	return {'Hello': 'Quenedi API'}


@app.get('/version')
def version():
	return {'version': VERSION}


def _check_user_access(claims):
	user_group = claims['cognito:groups'][0]
	if user_group not in get_user_groups(claims):
		raise HTTPException(status_code=401, detail='not allowed')


@app.get('/buckets')
async def get_buckets(Authorization: AuthHeader):
	claims = auth(Authorization)
	policies = get_user_policies(claims)
	buckets = get_available_buckets(policies)
	buckets.sort()
	return buckets


@app.get('/listGroups')
async def list_groups(Authorization: AuthHeader):
	claims = auth(Authorization)
	groups = get_user_groups(claims)
	return groups


@app.get('/listUser/{group}')
async def list_users(group: str, Authorization: AuthHeader):
	claims = auth(Authorization)
	_check_user_access(claims)
	users = list_group_users(group)
	return users


@app.post('/setUserPassword')
async def set_password(payload: User, Authorization: AuthHeader):
	claims = auth(Authorization)
	_check_user_access(claims)
	response = set_user_password(payload.username, payload.password)

	return response


@app.post('/createUser/{group}')
async def create_user_in_group(group: str, payload: User, Authorization: Annotated[str | None, Header()] = None):
	claims = auth(Authorization)
	_check_user_access(claims)
	response = create_user(
		group=group,
		username=payload.username,
		email=payload.email,
		given_name=payload.given_name,
		family_name=payload.family_name,
		password=payload.password,
	)
	return response


@app.post('/deleteUser')
async def delete_user(payload: Username, Authorization: AuthHeader):
	claims = auth(Authorization)
	_check_user_access(claims)
	user_name = claims['cognito:username']
	if payload.username == user_name:
		raise HTTPException(status_code=403, detail='cannot delete yourself')

	response = delete_user_by_username(payload.username)
	return response


#
# Quetzal Api run
#


def on_ecs(infra: Infra) -> bool:
	return infra.lower() == 'ecs'


# get the infra (ecs or lambda)
@app.get('/run/{function_name}/infra', response_model=Infra)
def get_infra(function_name: str):
	ecs_tasks = list_tasks_revisions(function_name)
	if len(ecs_tasks) > 0:
		return 'ecs'
	else:
		return 'lambda'


@app.get('/run/{function_name}/{infra}/tag')
def get_ecs_task_image_tag(function_name: str, infra: Infra, Authorization: AuthHeader):
	auth(Authorization)
	if on_ecs(infra):
		return get_image_tag(function_name)
	else:
		return get_lambda_image_tag(function_name)


# get steps
@app.get('/run/{function_name}/{infra}/steps', response_model=DisplayStepsDict)
def get_steps_definition(function_name: str, infra: Infra):
	if on_ecs(infra):
		res = get_ecs_steps(bucket=function_name)
		return res
	else:
		res = get_stepfunctions_steps(function_name=function_name)
		return res


# start
@app.post('/run/{function_name}/{infra}', response_model=str)
def run_task(function_name: str, infra: Infra, payload: RunPayload, Authorization: AuthHeader):
	# auth user
	claims = auth(Authorization)
	# access control. make sure user has acces to the model (to its bucket)
	get_bucket = get_ecs_bucket if on_ecs(infra) else get_lambda_bucket
	bucket = get_bucket(function_name)
	checkAccessToBucket(claims, bucket)

	if on_ecs(infra):
		job_id = run_ecs(
			function_name=function_name,
			scenario_path=payload.scenario_path,
			launcher_arg=payload.launcher_arg,
			steps=payload.steps,
			variants=payload.variants,
			metadata=payload.metadata,
		)
		# init step_status to new run
		step_status = StepStatusController(
			bucket_name=function_name, scenario=payload.scenario_path, metadata=payload.metadata
		)
		step_status.put_status(StepStatus())
	else:
		job_id = run_stepfunctions(
			function_name=function_name,
			scenario_path=payload.scenario_path,
			launcher_arg=payload.launcher_arg,
			variants=payload.variants,
			choice=payload.choice,
			authorization=Authorization,
			metadata=payload.metadata,
		)

	return job_id


# stop
@app.post('/run/{function_name}/{infra}/stop', response_model=bool)
def stop_task(function_name: str, infra: Infra, payload: StopPayload, Authorization: AuthHeader):
	auth(Authorization)
	job_id = payload.job_id
	if on_ecs(infra):
		return stop_ecs_task(function_name=function_name, job_id=job_id)
	else:
		return stop_stepfunctions(function_name=function_name, job_id=job_id)


# get status
@app.post('/run/{function_name}/{infra}/status', response_model=Status)
def get_status(function_name: str, infra: Infra, payload: PollPayload):
	job_id = payload.job_id
	scenario = payload.scenario_path
	if on_ecs(infra):
		ecs_status = get_ecs_status(function_name=function_name, job_id=job_id)
		# print(ecs_status)
		step_status = StepStatusController(bucket_name=function_name, scenario=scenario).get_status()
		# print(step_status)
		return Status(job_id=job_id, status=ecs_status, step_status=step_status)
	else:
		status = get_stepfunctions_status(job_id)
		return status


# get tasks aready running
@app.get('/run/{function_name}/{infra}/job_id/{scenario}', response_model=str)
def get_running_job_id(function_name: str, infra: Infra, scenario: str, Authorization: AuthHeader):
	auth(Authorization)
	if on_ecs(infra):
		return get_running_ecs_task(function_name=function_name, scenario=scenario)
	else:
		return get_running_stepfunctions(function_name=function_name, scenario=scenario)


handler = Mangum(app=app)
