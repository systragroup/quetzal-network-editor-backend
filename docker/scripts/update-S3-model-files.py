import json
import os
import sys

import boto3

# python update-S3-model-files.py quetzal_test base
# copy files from quetzal_test/scenarios/base/
# to base/ on s3.

s3 = boto3.resource('s3')
s3Client = boto3.client('s3')


def upload_info(bucket, scenario):
	import datetime

	info = {
		'description': '',
		'model_tag': '',
		'last_modified_date': datetime.datetime.now().isoformat(),
		'last_modified_email': '',
	}
	key = f'{scenario}/info.json'
	print('info', info)
	s3Client.put_object(Bucket=bucket, Key=key, Body=json.dumps(info))


def list_paths_in_directory(directory):
	file_paths = []
	for root, directories, files in os.walk(directory):
		for file_name in files:
			file_paths.append(os.path.join(root, file_name))
	return file_paths


def main():
	with open('.env') as f:
		for line in f:
			key, value = line.strip().split('=', 1)
			os.environ[key] = value

	bucket = s3.Bucket(os.environ['AWS_ECR_REPO_NAME'])
	for scenario in sys.argv[2:]:
		# Delete content
		for obj in bucket.objects.filter(Prefix=scenario + '/'):
			s3.Object(bucket.name, obj.key).delete()

		print(f'Updating {scenario} scenario')
		localpath = 'scenarios/' + scenario + '/'
		if not os.path.exists(localpath):
			print(f'Local path does not exists: {localpath}')
			continue
		if os.path.isdir(localpath):
			files = list_paths_in_directory(localpath)
			for file in files:
				print('upload:', file)
				bucket.upload_file(file, file[10:].replace(os.sep, '/'))
		upload_info(bucket.name, scenario)


if __name__ == '__main__':
	if len(sys.argv) < 3:
		print('Error: At least two argument is required.')
		print(f'Usage: python {sys.argv[0]} model_folder scenario1 [scenario2] ...')
		sys.exit(1)

	source = os.path.dirname(os.path.abspath(__file__))
	quetzal_root = os.path.abspath(os.path.join(source, '../../..'))
	os.chdir(os.path.abspath(os.path.join(quetzal_root, sys.argv[1])))
	main()
