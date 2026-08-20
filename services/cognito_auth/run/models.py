from enum import Enum
from typing import Literal, TypedDict

from pydantic import BaseModel

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


class StepStatus(BaseModel):
	step: str = ''
	error: str | None = None


class Status(BaseModel):
	job_id: str
	status: JobStatus
	step_status: StepStatus | None = None


# orchestrator payload
class Step(TypedDict):
	name: str
	path: str


# steps.json
class ModelStep(TypedDict):
	name: str
	steps: list[Step]


class RunPayload(BaseModel):
	scenario_path: str
	params: dict
	variants: list = []
	metadata: dict = {}
	steps: list[Step] = []  # for ECS
	choice: str = ''  # for sfn
	revision: str | None = None


class PollPayload(BaseModel):
	scenario_path: str
	job_id: str


class StopPayload(BaseModel):
	job_id: str


# stuff return to the front to show steps
class DisplayStep(TypedDict):
	name: str
	tasks: list[str]


type DisplayStepsDict = dict[str, list[DisplayStep]]


class Revision(BaseModel):
	revision: str
	tag: str
