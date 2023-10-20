import os
import requests
import jwt
import json
import boto3
from fastapi import  HTTPException


USER_POOL_ID = os.environ['USER_POOL_ID']
APP_CLIENT_ID = os.environ['APP_CLIENT_ID']
REGION = os.environ['REGION']

iam_client = boto3.client('iam')

def verify_cognito_token(token):
    # Your Cognito User Pool ID

    # Fetch the JSON Web Key Set (JWKS) from Cognito
    jwks_url = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json'
    jwks_response = requests.get(jwks_url)
    jwks_data = jwks_response.json()
    public_key = None
    for key in jwks_data['keys']:
        if key['kid'] == jwt.get_unverified_header(token)['kid']:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
            break
    if public_key:
        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=APP_CLIENT_ID,
            issuer=f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}',
            options={'verify_exp': True}
        )
        return decoded_token
    else:
        raise ValueError('Public key for token not found')

def auth(token):
    try:
        claims = verify_cognito_token(token)
    except jwt.ExpiredSignatureError:
          raise HTTPException(status_code=401,detail='Token has expired')
    except Exception as e:
        raise HTTPException(status_code=401,detail=f'Token validation failed: {e}')
    return claims

def get_policy_document(policy_arn):
    policy = iam_client.get_policy(PolicyArn=policy_arn)
    policy_version = iam_client.get_policy_version(
        PolicyArn = policy_arn, 
        VersionId = policy['Policy']['DefaultVersionId']
    )

    return policy_version['PolicyVersion']['Document']['Statement']

def get_policies_from_role(role_name):

     # Get the role's policies
    response = iam_client.list_attached_role_policies(RoleName=role_name)

    # Extract and print the attached policies
    attached_policies = response['AttachedPolicies']
    

    policies = []
    for pol in attached_policies:
        res = get_policy_document(pol['PolicyArn'])
        policies.append(res)
    return policies