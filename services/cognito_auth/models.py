from pydantic import BaseModel
from enum import Enum
from typing import Optional, Literal


ECSTaskStatus = Literal[
	'PROVISIONING', 'PENDING', 'ACTIVATING', 'RUNNING', 'DEACTIVATING', 'STOPPING', 'DEPROVISIONING', 'STOPPED'
]


class JobStatus(Enum):
	PREPARING = 'PREPARING'
	RUNNING = 'RUNNING'
	SUCCESS = 'SUCCESS'
	FAILED = 'FAILED'
	STOPPING = 'STOPPING'


class StepStatus(BaseModel):
	step: str = ''
	error: Optional[str] = None


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
