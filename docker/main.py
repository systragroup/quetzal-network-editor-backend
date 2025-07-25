import sys
import os
import json
import boto3
import shutil
import time
from typing import Dict
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT

sys.path.insert(0, os.path.abspath('quetzal'))

s3 = boto3.resource('s3')


def download_s3_folder(bucket_name, s3_folder, local_dir='/tmp'):
	"""
	Download the contents of a folder directory
	Args:
	    bucket_name: the name of the s3 bucket
	    s3_folder: the folder path in the s3 bucket
	    local_dir: a relative or absolute directory path in the local file system
	"""
	bucket = s3.Bucket(bucket_name)
	for obj in bucket.objects.filter(Prefix=s3_folder):
		target = obj.key if local_dir is None else os.path.join(local_dir, os.path.relpath(obj.key, s3_folder))
		if not os.path.exists(os.path.dirname(target)):
			os.makedirs(os.path.dirname(target))
		if obj.key[-1] == '/':
			continue
		bucket.download_file(obj.key, target)


def upload_s3_folder(bucket_name, prefix, local_dir='/tmp', metadata={}):
	"""
	Upload the contents of a folder directory to S3
	Args:
	    bucket_name: the name of the s3 bucket
	    s3_folder: the folder path in the s3 bucket
	    local_dir: a relative or absolute directory path in the local file system
	"""
	bucket = s3.Bucket(bucket_name)
	for root, _, files in os.walk(local_dir):
		for file in files:
			local_path = os.path.join(root, file)
			folder = ''
			if root != local_dir:  # if not. return '.' and the os.path.join send root files to ./
				folder = os.path.relpath(root, local_dir)
			s3_path = os.path.join(prefix, folder, file)
			bucket.upload_file(local_path, s3_path, ExtraArgs={'Metadata': metadata})


def upload_logs_to_s3(bucket_name, prefix, name, body, metadata={}):
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


def handler(event, context):
	t0 = time.time()
	notebook = event['notebook_path']
	print(event)
	bucket_name = os.environ['BUCKET_NAME']
	os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib-cache'
	# Move (and download) model data and inputs to ephemeral storage
	t_clean = time.time()
	clean_folder()  # Clean ephemeral storage
	print('clean: {} seconds'.format(time.time() - t_clean))
	t_copy = time.time()
	try:
		shutil.move('./inputs', '/tmp/inputs')
	except:
		print('cannot copy local docker inputs/ folder. its maybe missing on purpose')
	print('copy docker files: {} seconds'.format(time.time() - t_copy))

	download_s3_folder(bucket_name, event['scenario_path_S3'])
	t1 = time.time()
	print('Download inputs from s3 and docker image: {} seconds'.format(t1 - t0))

	arg = json.dumps(event['launcher_arg'])
	print(arg)

	pyfile = os.path.join('/tmp', os.path.basename(notebook).replace('.ipynb', '.py'))
	if notebook.endswith('.ipynb'):
		os.system('jupyter nbconvert --to python %s --output %s' % (notebook, pyfile))
	else:
		os.system('cp %s %s' % (notebook, pyfile))
	cwd = os.path.dirname(notebook)
	if cwd == '':
		cwd = '/'
	command_list = ['python', pyfile, arg]
	my_env = os.environ.copy()
	my_env['PYTHONPATH'] = os.pathsep.join(sys.path)

	t2 = time.time()
	print('Notebook conversion: {} seconds'.format(t2 - t1))

	process = Popen(command_list, stdout=PIPE, stderr=STDOUT, env=my_env, cwd=cwd)
	process.wait(timeout=800)

	content = process.stdout.read().decode('utf-8')

	logfile = os.path.basename(pyfile).replace('.py', '.txt')
	upload_logs_to_s3(bucket_name, event['scenario_path_S3'], logfile, content, metadata=event.get('metadata', {}))

	t3 = time.time()
	print('Notebook execution: {} seconds'.format(t3 - t2))

	print(content)
	# TODO: better parse :
	# if we print 'Error' and there is no end_of_notebook. we will raise an error...
	if 'Error' in content and 'end_of_notebook' not in content:
		raise RuntimeError(format_error(content))

	# Write model version in info.json
	image_tag = os.environ.get('IMAGE_TAG', None)
	if image_tag:
		path = Path('/tmp/info.json')
		data = json.loads(path.read_text()) if path.exists() else {}
		data['model_tag'] = image_tag
		path.write_text(json.dumps(data, indent=2))

	# if notebook return some args. add them
	event = get_return_args(event, content)
	# upload files to S3 (all except inputs)
	os.remove(pyfile)
	try:  # dont upload inputs
		shutil.rmtree('/tmp/inputs')
	except:
		pass
	try:  # dont reupload logs.
		shutil.rmtree('/tmp/logs')
	except:
		pass

	upload_s3_folder(bucket_name, event['scenario_path_S3'], metadata=event.get('metadata', {}))
	t4 = time.time()
	print('Upload to S3: {} seconds'.format(t4 - t3))
	print('Total excecution time: {} seconds'.format(t4 - t0))

	return event


def deep_update(mapping: Dict, *updating_mappings) -> Dict:
	# update a nested dict
	# from Pydantic
	# https://github.com/pydantic/pydantic/blob/fd2991fe6a73819b48c906e3c3274e8e47d0f761/pydantic/utils.py#L200
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
