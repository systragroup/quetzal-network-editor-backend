from pydantic import BaseModel
from enum import Enum
from typing import Optional, Literal, TypedDict
from step_status import StepStatus

type StepfunctionsStatus = Literal[
	'RUNNING',
	'SUCCEEDED',
	'FAILED',
	'TIMED_OUT',
	'ABORTED',
	'PENDING_REDRIVE',
]


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
type Infra = Literal['ecs', 'lambda']


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


# orchestrator payload
class Step(TypedDict):
	name: str
	path: str


# steps.json
class ModelStep(TypedDict):
	name: str
	steps: list[Step]


class RunPayload(BaseModel):
	function_name: str
	scenario_path: str
	launcher_arg: dict
	variants: list = []
	metadata: dict = {}
	steps: list[Step] = []  # for ECS
	choice: str = ''  # for sfn


# stuff return to the front to show steps
class DisplayStep(TypedDict):
	name: str
	tasks: list[str]


type DisplayStepsDict = dict[str, list[DisplayStep]]
