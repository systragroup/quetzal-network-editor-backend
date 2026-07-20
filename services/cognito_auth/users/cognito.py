import boto3
import os
from auth import get_user_policies, get_available_buckets
from fastapi import HTTPException

USER_POOL_ID = os.environ['USER_POOL_ID']

client = boto3.client('cognito-idp')


def get_user_groups(claims) -> list[str]:
	# return the list of available user_groups for a given user
	# this is Bucket based. so you only see groups with the name == bucket name
	user_group = claims['cognito:groups'][0]
	_all_groups = [group['GroupName'] for group in client.list_groups(UserPoolId=USER_POOL_ID)['Groups']]
	if user_group == 'admin':
		return _all_groups
	else:
		# list policies to find all available buckets
		policies = get_user_policies(claims)
		buckets = get_available_buckets(policies)
		_all_groups = [group['GroupName'] for group in client.list_groups(UserPoolId=USER_POOL_ID)['Groups']]
		available_groups = [name for name in _all_groups if name in buckets]
		# insert actual user group as first in the list
		available_groups = [name for name in available_groups if name != user_group]
		available_groups = [user_group, *available_groups]
		return available_groups


def list_group_users(group: str) -> list[dict]:
	# Can be paginated with NextToken
	response = client.list_users_in_group(UserPoolId=USER_POOL_ID, GroupName=group)
	temp_users = response['Users']
	while 'NextToken' in response.keys():
		nextToken = response['NextToken']
		response = client.list_users_in_group(UserPoolId=USER_POOL_ID, GroupName=group, NextToken=nextToken)
		temp_users.extend(response['Users'])

	users = []
	for user in temp_users:
		attrs_dict = {attr['Name']: attr['Value'] for attr in user['Attributes']}
		user.update(attrs_dict)
		user.pop('Attributes', None)
		users.append(user)
	users.sort(key=lambda x: x['Username'])
	return users


def set_user_password(username: str, password: str):
	try:
		return client.admin_set_user_password(
			UserPoolId=USER_POOL_ID, Username=username, Password=password, Permanent=False
		)

	except Exception as err:
		raise HTTPException(status_code=400, detail=str(err))


def add_user_to_group(group: str, username: str):
	response = client.admin_add_user_to_group(UserPoolId=USER_POOL_ID, Username=username, GroupName=group)
	return response


def create_user(
	group: str, username: str, email: str | None, given_name: str | None, family_name: str | None, password: str
):
	try:
		resp = client.admin_create_user(
			UserPoolId=USER_POOL_ID,
			Username=username,
			UserAttributes=[
				{'Name': 'email', 'Value': email},
				{'Name': 'email_verified', 'Value': 'true'},
				{'Name': 'given_name', 'Value': given_name},
				{'Name': 'family_name', 'Value': family_name},
			],
			TemporaryPassword=password,
		)
	except Exception as err:
		raise HTTPException(status_code=400, detail=str(err))
	response = add_user_to_group(group=group, username=username)
	return response


def delete_user_by_username(username: str):
	try:
		response = client.admin_delete_user(UserPoolId=USER_POOL_ID, Username=username)
		return response
	except Exception as err:
		raise HTTPException(status_code=400, detail=str(err))
