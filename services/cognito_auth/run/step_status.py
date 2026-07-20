import os
import json
import boto3
from dotenv import load_dotenv
from .models import StepStatus


load_dotenv()
REGION = os.environ['REGION']
s3 = boto3.client('s3', region_name=REGION)


class StepStatusController:
	def __init__(self, bucket_name: str, scenario: str, metadata: dict = {}):
		self.bucket_name = bucket_name
		self.scenario = scenario
		self.metadata = metadata
		self.status_key = os.path.join(self.scenario, 'status.json')

		session = boto3.Session()
		self.s3_client = session.client('s3')

	def put_status(self, step_status: StepStatus = StepStatus()):
		self.s3_client.put_object(
			Body=json.dumps(step_status.model_dump(), indent=2),
			Bucket=self.bucket_name,
			Key=self.status_key,
			CacheControl='no-cache',
			Metadata=self.metadata,
		)

	def get_status(self) -> StepStatus | None:
		try:
			response = s3.get_object(Bucket=self.bucket_name, Key=self.status_key)
			body = response['Body'].read().decode('utf-8')
			return StepStatus(**json.loads(body))
		except:
			return None
