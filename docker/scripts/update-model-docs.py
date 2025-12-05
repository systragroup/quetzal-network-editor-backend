import os
import sys
import boto3

# python update-S3-model-files.py quetzal_test base
# copy files from quetzal_test/scenarios/base/
# to base/ on s3.

s3 = boto3.resource('s3')


def list_paths_in_directory(directory):
	file_paths = []
	for root, directories, files in os.walk(directory):
		for file_name in files:
			file_paths.append(os.path.join(root, file_name))
	return file_paths


def main():
	localpath = sys.argv[2]
	with open('.env') as f:
		for line in f:
			key, value = line.strip().split('=', 1)
			os.environ[key] = value

	bucket = s3.Bucket(os.environ['AWS_BUCKET_NAME'])
	prefix = '_common/docs/'
	# Delete content
	for obj in bucket.objects.filter(Prefix=prefix):
		s3.Object(bucket.name, obj.key).delete()
		pass

	print(f'Updating docs from {localpath}')
	if not os.path.exists(localpath):
		print(f'Local path does not exists: {localpath}')
		return
	if os.path.isdir(localpath):
		files = list_paths_in_directory(localpath)
		for file in files:
			s3_name = prefix + file[len(localpath) + 1 :].replace(os.sep, '/')
			print('upload:', file, 'to', s3_name)

			bucket.upload_file(file, s3_name)


if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('Error: At least two argument is required.')
		print('Usage: python {name} model_folder doc_relative_path ...'.format(name=sys.argv[0]))
		sys.exit(1)

	source = os.path.dirname(os.path.abspath(__file__))
	quetzal_root = os.path.abspath(os.path.join(source, '../../..'))
	os.chdir(os.path.abspath(os.path.join(quetzal_root, sys.argv[1])))
	main()
