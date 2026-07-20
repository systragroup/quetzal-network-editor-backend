from .models import ECSTaskStatus, StepfunctionsStatus, JobStatus


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


def map_stepfunctions_status(status: StepfunctionsStatus, exit_code: int | None = None) -> JobStatus:
	if status in ['RUNNING', 'PENDING_REDRIVE']:
		return JobStatus.RUNNING
	if status in ['FAILED', 'TIMED_OUT', 'ABORTED']:
		return JobStatus.FAILED
	if status in ['SUCCEEDED']:
		return JobStatus.SUCCESS
	return JobStatus.UNKNOWN
