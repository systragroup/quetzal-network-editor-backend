import os
import sys
import boto3
# python update-model-config.py <model_folder>
# push modelConfig.json to model _common/modelConfig.json

s3 = boto3.resource('s3')


def main():
	with open('.env') as f:
		for line in f:
			key, value = line.strip().split('=', 1)
			os.environ[key] = value

	bucket = s3.Bucket(os.environ['AWS_BUCKET_NAME'])
	prefix = '_common/'
	file = 'modelConfig.json'

	if not os.path.exists(file):
		print(f'Local path does not exists: {file}')
		return
	print(f'Updating  {file}')
	s3_name = prefix + file
	print('upload:', file, 'to', s3_name)

	bucket.upload_file(file, s3_name)


if __name__ == '__main__':
	print(sys.argv)
	if len(sys.argv) != 2:
		print('Error: At least two argument is required.')
		print('Usage: python {name} model_folder...'.format(name=sys.argv[0]))
		sys.exit(1)

	source = os.path.dirname(os.path.abspath(__file__))
	quetzal_root = os.path.abspath(os.path.join(source, '../../..'))
	os.chdir(os.path.abspath(os.path.join(quetzal_root, sys.argv[1])))
	main()
