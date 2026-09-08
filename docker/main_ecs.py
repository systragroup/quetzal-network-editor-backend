import json
import os
import shutil
import signal
import sys
import time
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen, TimeoutExpired

import boto3


class StatusController:
	def __init__(self, bucket_name: str, scenario: str, metadata: dict = {}):
		self.bucket_name = bucket_name
		self.scenario = scenario
		self.metadata = metadata
		self.status_key = os.path.join(self.scenario, 'status.json')

		session = boto3.Session()
		self.s3_client = session.client('s3')

	def put_status(self, step: str, error: str | None = None):
		status = {'step': step, 'error': error}
		self.s3_client.put_object(
			Body=json.dumps(status, indent=2),
			Bucket=self.bucket_name,
			Key=self.status_key,
			CacheControl='no-cache',
			Metadata=self.metadata,
		)


class S3Controller:
	def __init__(self, bucket_name: str, scenario: str, metadata: dict = {}):
		self.bucket_name = bucket_name
		self.scenario = scenario
		self.metadata = metadata
		self.local_dir = '/app'

	def download_folder(self):
		_download_s3_folder(self.bucket_name, self.scenario, local_dir=self.local_dir)

	def upload_folder(self, folder):
		_upload_s3_folder(
			self.bucket_name,
			self.scenario,
			folder=os.path.join('/app', folder),
			metadata=self.metadata,
		)

	def upload_logs(self, name: str, body: str):
		_upload_logs_to_s3(self.bucket_name, self.scenario, name, body, self.metadata)


def _download_s3_folder(bucket_name, s3_folder, local_dir='/app'):
	"""
	Download the contents of a folder directory
	Args:
	    bucket_name: the name of the s3 bucket
	    s3_folder: the folder path in the s3 bucket
	    local_dir: a relative or absolute directory path in the local file system
	"""
	s3 = boto3.resource('s3')
	bucket = s3.Bucket(bucket_name)  # type: ignore
	for obj in bucket.objects.filter(Prefix=s3_folder):
		target = obj.key if local_dir is None else os.path.join(local_dir, os.path.relpath(obj.key, s3_folder))
		if not os.path.exists(os.path.dirname(target)):
			os.makedirs(os.path.dirname(target))
		if obj.key[-1] == '/':
			continue
		bucket.download_file(obj.key, target)


def _upload_s3_folder(bucket_name, prefix, folder='/app', metadata={}):
	"""
	Upload the contents of a folder directory to S3
	Args:
	    bucket_name: the name of the s3 bucket
	    s3_folder: the folder path in the s3 bucket
	    local_dir: a relative or absolute directory path in the local file system
	"""
	s3 = boto3.resource('s3')
	bucket = s3.Bucket(bucket_name)  # type: ignore
	for root, _, files in os.walk(folder):
		for file in files:
			local_path = os.path.join(root, file)
			folder = ''
			if root != folder:  # if not. return '.' and the os.path.join send root files to ./
				folder = os.path.relpath(root, folder)
			s3_path = os.path.join(prefix, folder, file)
			bucket.upload_file(local_path, s3_path, ExtraArgs={'Metadata': metadata})


def _upload_logs_to_s3(bucket_name, prefix, name, body, metadata={}):
	# to logs/log.txt
	session = boto3.Session()
	s3 = session.client('s3')
	s3.put_object(
		Body=body,
		Bucket=bucket_name,
		Key=os.path.join(prefix, 'logs/', name),
		CacheControl='no-cache',
		Metadata=metadata,
	)


def clean_folder(folder='/tmp'):
	for filename in os.listdir(folder):
		file_path = os.path.join(folder, filename)
		try:
			if os.path.isfile(file_path) or os.path.islink(file_path):
				os.unlink(file_path)
			elif os.path.isdir(file_path):
				shutil.rmtree(file_path)
		except Exception as e:
			print('Failed to delete %s. Reason: %s' % (file_path, e))


def format_error(err):
	# return the error starting a Traceback.
	part = err.partition('Traceback')
	res = part[1] + part[2]
	if len(res) > 0:
		return res
	else:
		return part[0]


def orchestrator():
	kwargs = os.environ
	steps = json.loads(kwargs['steps'])
	bucket_name = kwargs['BUCKET_NAME']
	scenario_path = kwargs.get('scenario_path', '')
	launcher_arg = kwargs['launcher_arg']

	launcher_arg = json.loads(kwargs['launcher_arg'])
	training_folder = launcher_arg.pop('training_folder', None)

	metadata = json.loads(kwargs.get('metadata', '{}'))

	# os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib-cache'
	status = StatusController(bucket_name, scenario_path, metadata)
	storage = S3Controller(bucket_name=bucket_name, scenario=scenario_path, metadata=metadata)

	# Move (and download) model data and inputs to ephemeral storage
	t0 = time.time()
	# clean_folder()  # Clean ephemeral storage
	# if os.path.exists('/inputs'):  # move docker inputs/ folder
	# 	shutil.move('./inputs', '/tmp/inputs')
	storage.download_folder()
	print(f'Download inputs: {time.time() - t0} seconds')
	t1 = time.time()

	# run
	for step in steps:
		print(step)
		step_name = step['name']
		notebook_path = step['path']
		status.put_status(step_name)
		try:
			run_step(notebook=notebook_path, launcher_arg=launcher_arg, storage=storage)
		except Exception as err:
			status.put_status(step_name, str(err))
			raise

	t2 = time.time()

	print(f'steps total time: {t2 - t1} seconds')

	# upload files to S3)
	if os.path.exists('/app/inputs'):  # except inputs
		shutil.rmtree('/app/inputs')

	# Write model version in info.json
	image_tag = os.environ.get('IMAGE_TAG', None)
	if image_tag:
		path = Path('/app/info.json')
		data = json.loads(path.read_text()) if path.exists() else {}
		data['model_tag'] = image_tag
		path.write_text(json.dumps(data, indent=2))

	storage.upload_folder(folder='outputs/')

	t3 = time.time()
	print(f'Upload to S3: {t3 - t2} seconds')

	print(f'total execution time: {t3 - t0} seconds')


def run_step(notebook: str, launcher_arg: str, storage: S3Controller):
	t1 = time.time()
	print(launcher_arg)

	pyfile = notebook.replace('.ipynb', '.py')

	print(notebook)
	print(pyfile)

	if notebook.endswith('.ipynb'):
		os.system('jupyter nbconvert --to python %s' % (notebook))

	command_list = ['python', os.path.basename(pyfile), json.dumps(launcher_arg)]
	my_env = os.environ.copy()
	my_env['PYTHONPATH'] = os.pathsep.join(sys.path)

	t2 = time.time()
	print(f'Notebook conversion: {t2 - t1} seconds')

	print('Command', command_list)

	process = Popen(command_list, stdout=PIPE, stderr=STDOUT, env=my_env, cwd=os.path.dirname(pyfile))

	try:
		stdout_bytes, _ = process.communicate(timeout=None)

	except TimeoutExpired:
		print('Process timed out. Killing process group...')
		process.kill()

		stdout_bytes, _ = process.communicate()
		stdout = stdout_bytes.decode('utf-8', errors='replace')

		logfile = os.path.basename(pyfile).replace('.py', '.txt')
		storage.upload_logs(logfile, stdout)
		raise TimeoutError('Notebook execution exceeded timeout')

	stdout = stdout_bytes.decode('utf-8', errors='replace')

	logfile = os.path.basename(pyfile).replace('.py', '.txt')
	storage.upload_logs(logfile, stdout)
	# clean
	# os.remove(pyfile)
	if os.path.exists('/app/logs'):
		shutil.rmtree('/app/logs')

	t3 = time.time()
	print(f'Notebook execution: {t3 - t2} seconds')

	print(stdout)
	# parse error. if return_code!=0 (there is an error)
	# doule check for [ERROR]. also: do not throw error for end_of_notebook
	if process.returncode != 0 and 'end_of_notebook' not in stdout:
		raise RuntimeError(format_error(stdout))

	# TODO: add those to the env_variable for next step.
	# if notebook return some args. add them
	# event = get_return_args(event, content)


def deep_update(mapping: dict, *updating_mappings) -> dict:
	# update a nested dict
	# (from Pydantic) https://github.com/pydantic/pydantic/blob/fd2991fe6a73819b48c906e3c3274e8e47d0f761/pydantic/utils.py#L200
	updated_mapping = mapping.copy()
	for updating_mapping in updating_mappings:
		for k, v in updating_mapping.items():
			if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
				updated_mapping[k] = deep_update(updated_mapping[k], v)
			else:
				updated_mapping[k] = v
	return updated_mapping


def get_return_args(event, content):
	# in notebook if print("RETURN:", dict) add it to event to the next step function.
	for line in content.splitlines():
		if line.startswith('RETURN:'):
			import ast

			returned_arg = line[7:]  # Remove "RETURN:" prefix
			# transform string to dict
			returned_arg = ast.literal_eval(returned_arg)
			event = deep_update(event, returned_arg)
	return event


def start_timeout():
	"""
	will throw exception when timeout (minutes) is reached
	"""

	timeout = float(os.environ.get('TIME_LIMIT', '60'))

	def timeout_handler(signum, frame):
		raise TimeoutError(f'Timeout reached ({timeout} mins)')

	signal.signal(signal.SIGALRM, timeout_handler)
	signal.alarm(int(timeout * 60))


if __name__ == '__main__':
	print('env', os.environ)
	start_timeout()
	orchestrator()
