import os
import sys
import boto3

# python update-S3-model-files.py quetzal_test base
# copy files from quetzal_test/scenarios/base/
# to base/ on s3.

s3 = boto3.resource('s3')


def folder_exists(bucket, prefix):
	for obj in bucket.objects.filter(Prefix=prefix):
		return True  # At least one object exists with this prefix
	return False


def main():
	with open('.env') as f:
		for line in f:
			key, value = line.strip().split('=', 1)
			os.environ[key] = value
	bucket = s3.Bucket(os.environ['AWS_BUCKET_NAME'])
	for scenario in sys.argv[2:]:
		lock_key = f'{scenario}/.lock'
		print(f'locking: {scenario}')
		if folder_exists(bucket, scenario):
			s3.Object(bucket.name, lock_key).put(Body=b'')
			print('locked!')
		else:
			print('scenario doesnt exist')


if __name__ == '__main__':
	if len(sys.argv) < 3:
		print('Error: At least two argument is required.')
		print('Usage: python {name} model_folder scenario1 [scenario2] ...'.format(name=sys.argv[0]))
		sys.exit(1)

	source = os.path.dirname(os.path.abspath(__file__))
	quetzal_root = os.path.abspath(os.path.join(source, '../../..'))
	os.chdir(os.path.abspath(os.path.join(quetzal_root, sys.argv[1])))
	main()
