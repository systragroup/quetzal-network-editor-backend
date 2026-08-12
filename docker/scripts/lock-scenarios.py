import json
import os
import sys

import boto3

s3Client = boto3.client('s3')


def scenario_exists(bucket, scenario):
	response = s3Client.list_objects_v2(Bucket=bucket, Prefix=scenario, MaxKeys=1)
	exists = 'Contents' in response
	return exists


def main():
	with open('.env') as f:
		for line in f:
			key, value = line.strip().split('=', 1)
			os.environ[key] = value
	bucket = os.environ['AWS_ECR_REPO_NAME']
	key = '_common/lock.json'
	try:
		response = s3Client.get_object(Bucket=bucket, Key=key)
		content = response['Body'].read()
		lock_list = json.loads(content.decode('utf-8'))
	except:
		lock_list = ['base']
	for scenario in sys.argv[2:]:
		if not scenario_exists(bucket, scenario):
			print(f'scenario {scenario} doesnt exist')
			continue
		if scenario in lock_list:
			print(f'scenario {scenario} already locked')
			continue

		lock_list.append(scenario)
		print(f'locking: {scenario}')
	s3Client.put_object(Bucket=bucket, Key=key, Body=json.dumps(lock_list))


if __name__ == '__main__':
	if len(sys.argv) < 3:
		print('Error: At least two argument is required.')
		print(f'Usage: python {sys.argv[0]} model_folder scenario1 [scenario2] ...')
		sys.exit(1)

	source = os.path.dirname(os.path.abspath(__file__))
	quetzal_root = os.path.abspath(os.path.join(source, '../../..'))
	os.chdir(os.path.abspath(os.path.join(quetzal_root, sys.argv[1])))
	main()
