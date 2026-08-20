import boto3

ecr = boto3.client('ecr')


def list_ecr_images_tag(function_name: str):
	# return list of tags
	response = ecr.list_images(repositoryName=function_name, filter={'tagStatus': 'TAGGED'})
	tags = [image['imageTag'] for image in response['imageIds'] if 'imageTag' in image]
	return tags
