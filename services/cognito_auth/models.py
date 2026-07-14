from pydantic import BaseModel
from enum import Enum
from typing import Optional, Literal
from step_status import StepStatus


type ECSTaskStatus = Literal[
	'PROVISIONING',
	'PENDING',
	'ACTIVATING',
	'RUNNING',
	'DEACTIVATING',
	'STOPPING',
	'DEPROVISIONING',
	'STOPPED',
]


class JobStatus(Enum):
	UNKNOWN = 'UNKNOWN'
	PREPARING = 'PREPARING'
	RUNNING = 'RUNNING'
	SUCCESS = 'SUCCESS'
	FAILED = 'FAILED'
	STOPPING = 'STOPPING'


class Status(BaseModel):
	job_id: str
	status: JobStatus
	step_status: Optional[StepStatus] = None


class RunPayload(BaseModel):
	function_name: str
	scenario_path: str
	steps: list
	launcher_arg: dict
	variants: list = []
	metadata: dict = {}


def map_ecs_status(ecs_status: ECSTaskStatus, exit_code: int | None = None) -> JobStatus:
	if ecs_status in ['PROVISIONING', 'PENDING', 'ACTIVATING']:
		return JobStatus.PREPARING
	if ecs_status in ['RUNNING']:
		return JobStatus.RUNNING
	if ecs_status in ['DEACTIVATING', 'STOPPING', 'DEPROVISIONING']:
		return JobStatus.STOPPING
	if ecs_status in ['STOPPED']:
		if exit_code == 0:
			return JobStatus.SUCCESS
		else:
			return JobStatus.FAILED
	return JobStatus.UNKNOWN
