import os
import json
import boto3
from dotenv import load_dotenv
from models import JobStatus, DisplayStepsDict, DisplayStep, ModelStep
from mappers import map_ecs_status

load_dotenv()
REGION = os.environ['REGION']
ACCOUNT = os.environ['ACCOUNT_ID']
ecs = boto3.client('ecs', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)


def get_cluster_name(function_name: str) -> str:
	return f'arn:aws:ecs:{REGION}:{ACCOUNT}:cluster/{function_name}'


def get_task_definition_name(function_name: str) -> str:
	return f'arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/{function_name}-task'


def run_ecs(
	function_name: str, scenario_path: str, launcher_arg: dict, steps: list, variants: list, metadata: dict
) -> str:
	cluster = get_cluster_name(function_name)
	task_definition = get_task_definition_name(function_name)
	IMAGE_TAG = get_image_tag(function_name)
	response = ecs.run_task(
		cluster=cluster,
		launchType='FARGATE',
		taskDefinition=task_definition,
		count=1,
		networkConfiguration={
			'awsvpcConfiguration': {
				'subnets': ['subnet-04ff36f2b80327321'],
				'securityGroups': ['sg-087728e78f1a2c4c2'],
				'assignPublicIp': 'ENABLED',
			}
		},
		overrides={
			'containerOverrides': [
				{
					'name': function_name,
					'environment': [
						{'name': 'scenario_path', 'value': str(scenario_path)},
						{'name': 'steps', 'value': json.dumps(steps)},
						{'name': 'launcher_arg', 'value': json.dumps(launcher_arg)},
						{'name': 'variants', 'value': json.dumps(variants)},
						{'name': 'metadata', 'value': json.dumps(metadata)},
						{'name': 'IMAGE_TAG', 'value': IMAGE_TAG},
					],
				}
			]
		},
	)
	job_id = response['tasks'][0]['taskArn']

	return job_id


def get_ecs_status(function_name: str, job_id: str) -> JobStatus:
	cluster = get_cluster_name(function_name)
	response = ecs.describe_tasks(cluster=cluster, tasks=[job_id])
	task = response['tasks'][0]
	container = task['containers'][0]
	exit_code = container.get('exitCode')
	# reason = task.get('stoppedReason')
	# stop_code = task.get('stopCode')
	status = map_ecs_status(task['lastStatus'], exit_code)

	return status


def stop_ecs_task(function_name: str, job_id: str) -> bool:
	cluster = get_cluster_name(function_name)
	try:
		ecs.stop_task(cluster=cluster, task=job_id, reason='User cancelled job')
		return True
	except Exception as err:
		print(err)
		return False


def _list_ecs_tasks(function_name: str, desired_status: str = 'RUNNING') -> list[str]:
	cluster = get_cluster_name(function_name)
	response = ecs.list_tasks(cluster=cluster, desiredStatus=desired_status)
	return response['taskArns']


def get_running_ecs_task(function_name: str, scenario: str) -> str:
	arn_list = _list_ecs_tasks(function_name, 'RUNNING')
	if len(arn_list) == 0:
		return ''
	cluster = get_cluster_name(function_name)
	response = ecs.describe_tasks(cluster=cluster, tasks=arn_list)
	for task in response['tasks']:
		envs = task['overrides']['containerOverrides'][0]['environment']
		filtered_envs = [v for v in envs if v['name'] == 'scenario_path']
		if len(filtered_envs) > 0:
			running_scen = filtered_envs[0]['value'].strip('/')
			if running_scen == scenario:
				return task['taskArn']
	return ''


def list_tasks_revisions(function_name: str) -> list[str]:
	definition_name = f'{function_name}-task'
	response = ecs.list_task_definitions(
		familyPrefix=definition_name,
		sort='DESC',
	)
	return response['taskDefinitionArns']


def get_image_tag(function_name: str) -> str:
	# get tag of first image: TODO: change if more docker per tasks in the future.
	task_definition = get_task_definition_name(function_name)
	task_def = ecs.describe_task_definition(taskDefinition=task_definition)['taskDefinition']
	tags = []  # TODO: can return a list of {revisionARN, imageTag} for front to chose. now only return latest tag
	revision_list = list_tasks_revisions(function_name)
	for revision in revision_list:
		task_def = ecs.describe_task_definition(taskDefinition=revision)['taskDefinition']
		container = task_def['containerDefinitions'][0]
		tag = container['image'].split(':')[-1]
		tags.append(tag)
		break

	return tags[0]


def get_ecs_steps(function_name: str) -> DisplayStepsDict:
	s3 = boto3.client('s3')
	response = s3.get_object(Bucket=function_name, Key='_common/steps.json')
	body = response['Body'].read().decode('utf-8')

	all_steps: list[ModelStep] = json.loads(body)
	steps_dict: DisplayStepsDict = {}
	for model_steps in all_steps:
		choice = model_steps['name']
		steps = model_steps['steps']
		display_steps: list[DisplayStep] = [{'name': s['name'], 'tasks': [s['name']]} for s in steps]
		steps_dict[choice] = display_steps
	return steps_dict
