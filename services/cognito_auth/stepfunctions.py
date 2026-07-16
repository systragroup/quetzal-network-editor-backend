import os
import boto3
from dotenv import load_dotenv
from models import DisplayStepsDict, Status
from step_status import StepStatus
from mappers import map_stepfunctions_status
import json

load_dotenv()
REGION = os.environ['REGION']
ACCOUNT = os.environ['ACCOUNT_ID']
lambda_client = boto3.client('lambda', region_name=REGION)
stepfunctions = boto3.client('stepfunctions')


def get_stepfunctions_name(function_name: str) -> str:
	return f'arn:aws:states:{REGION}:{ACCOUNT}:stateMachine:{function_name}'


def run_stepfunctions(
	function_name: str,
	scenario_path: str,
	launcher_arg: dict,
	variants: list,
	metadata: dict,
	choice: str,
	authorization: str,
) -> str:
	state_machine_arn = get_stepfunctions_name(function_name)
	response = stepfunctions.start_execution(
		stateMachineArn=state_machine_arn,
		input=json.dumps(
			{
				'authorization': authorization,
				'choice': choice,
				'scenario_path_S3': scenario_path,
				'launcher_arg': launcher_arg,
				'variants': variants,
				'metadata': metadata,
			},
		),
	)
	execution_arn = response['executionArn']

	return execution_arn


def stop_stepfunctions(function_name: str, job_id: str) -> bool:
	try:
		stepfunctions.stop_execution(executionArn=job_id)
		return True
	except Exception as err:
		print(err)
		return False


def get_running_stepfunctions(function_name: str, scenario: str) -> str:
	state_machine_arn = get_stepfunctions_name(function_name)
	response = stepfunctions.list_executions(stateMachineArn=state_machine_arn, statusFilter='RUNNING')
	execution_list = response['executions']
	scenario = scenario.strip('/')
	# return arn if its in the running list. else return ''
	for execution in execution_list:
		arn = execution['executionArn']
		resp = stepfunctions.describe_execution(executionArn=arn)
		scen = json.loads(resp['input'])['scenario_path_S3'].strip('/')
		if scenario == scen:
			return arn
	else:
		return ''


def get_lambda_image_tag(function_name: str) -> str:
	response = lambda_client.get_function(FunctionName=function_name)
	image = response['Code']['ImageUri']
	print(response)
	tag = image.split(':')[-1]

	return tag


def _get_stepfunctions_steps(definition, choice: str) -> list[dict]:
	current_step: str | None = definition['StartAt']
	states = definition['States']
	step_list = []
	while current_step is not None:
		step = states.get(current_step)
		step_type = step['Type']
		if step_type == 'Choice':
			if choice == 'default':
				next_step = step.get('Default', None)
			else:
				state_choices = step['Choices']
				next_choice = [c for c in state_choices if c['StringEquals'] == choice]
				next_step = next_choice[0].get('Next', None)
		elif step_type == 'Parallel':
			branches = step['Branches']
			tasks = [list(state['States'].keys()) for state in branches]
			transposed = [list(row) for row in zip(*tasks)]
			for parallel_step in transposed:
				name = ' | '.join(parallel_step)
				step_list.append({'name': name, 'tasks': parallel_step})
				next_step = step.get('Next', None)
		elif step_type == 'Map':
			iterator = step['Iterator']
			iterator_states = iterator['States']
			current = iterator['StartAt']
			while current is not None:
				step_list.append({'name': f'{current} (parallel)', 'tasks': [current]})
				current = iterator_states.get(current).get('Next', None)
			next_step = step.get('Next', None)
		else:
			next_step = step.get('Next', None)
			step_list.append({'name': current_step, 'tasks': [current_step]})
		current_step = next_step
	return step_list


def get_stepfunctions_steps(function_name: str) -> DisplayStepsDict:
	arn = get_stepfunctions_name(function_name)
	resp = stepfunctions.describe_state_machine(stateMachineArn=arn)
	definition = json.loads(resp['definition'])

	# get all choices
	choices = ['default']
	for key, item in definition['States'].items():
		if item['Type'] == 'Choice':
			choices.extend(choice['StringEquals'] for choice in item['Choices'])
	steps_dict = {}
	for choice in choices:
		steps = _get_stepfunctions_steps(definition, choice)
		steps_dict[choice] = steps
	return steps_dict


def _get_current_step(events) -> str:
	for event in events:
		event_type = event['type']
		if event_type == 'TaskStateEntered':
			return event['stateEnteredEventDetails']['name']
	else:
		return ''


def get_stepfunctions_status(job_id: str) -> Status:
	status = stepfunctions.describe_execution(executionArn=job_id)
	sfn_status = map_stepfunctions_status(status.get('status'))
	err = status.get('cause', None)

	events = stepfunctions.get_execution_history(executionArn=job_id, includeExecutionData=False, reverseOrder=True)[
		'events'
	]
	current_step = _get_current_step(events)
	step_status = StepStatus(step=current_step, error=err)

	return Status(job_id=job_id, status=sfn_status, step_status=step_status)
