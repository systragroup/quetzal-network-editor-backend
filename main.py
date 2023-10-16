
import os
from mangum import Mangum
from fastapi import  FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
from auth import auth, get_policies_from_role
from typing import Optional, Annotated


from middlewares.exception import ExceptionHandlerMiddleware

class User(BaseModel):
    username: str
    given_name:Optional[str]=None
    family_name:Optional[str]=None
    email: Optional[str]=None
    password: str

class Username(BaseModel):
    username: str


USER_POOL_ID = os.environ['USER_POOL_ID']

client = boto3.client('cognito-idp')



app = FastAPI()
# this is for AXIOS in vueJS (local dev)
origins = ['http://localhost:8081', 
           'https://localhost:8081', 
           'https://systragroup.github.io/quetzal-network-editor-dev/', 
           'https://systragroup.github.io/quetzal-network-editor/']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ExceptionHandlerMiddleware)

@app.get("/")
def read_root():
    return {"Hello": "Quenedi Cognito API"}

@app.get("/buckets/")
async def get_buckets(Authorization: Annotated[str | None, Header()] = None):
    claims = auth(Authorization)
    print(claims)
    try:
        role_arn = claims['cognito:roles'][0]
    except Exception as err:
        raise HTTPException(status_code=400,detail='User has no Cognito role')
    role_name = role_arn.split('/')[-1]
    try:
        policies = get_policies_from_role(role_name)
    except Exception as e:
        raise Exception('error listing role policies:', e)
    # get a list of all s3 buckets access ['arn:aws:s3:::quetzal-test/*, ...]
    s3_policies = []
    for policy in policies:
        if (policy[1]['Effect'] == 'Allow'):
            if type(policy[1]['Resource']) == list:
                s3_policies = s3_policies + policy[1]['Resource']
            else:
                s3_policies.append(policy[1]['Resource'])
    #remove arn:aws:s3::: and /*
    buckets = [pol[13:-2] for pol in s3_policies]
    buckets = [bucket for bucket in buckets if bucket not in ['quenedi-osm','quetzal-config']]
    buckets.sort()
    return buckets


@app.get("/listGroups/")
async def list_groups(Authorization: Annotated[str | None, Header()] = None):
    claims = auth(Authorization)
    user_group = claims['cognito:groups'][0]
    if user_group == 'admin':
        response = client.list_groups(UserPoolId=USER_POOL_ID)
        return [group['GroupName'] for group in response['Groups']]
    else:
        return [user_group]

@app.get("/listUser/{group}/")
async def list_users(group:str, Authorization: Annotated[str | None, Header()] = None):
    claims = auth(Authorization)
    user_group = claims['cognito:groups'][0]
    if (user_group != group) and (user_group != 'admin'):
        raise HTTPException(status_code=401,detail='not allowed')

    response = client.list_users_in_group(UserPoolId=USER_POOL_ID, GroupName=group)
    users=[]
    for user in response['Users']:
        attrs_dict = {attr['Name']:attr['Value'] for attr in user['Attributes']}
        user.update(attrs_dict)
        user.pop('Attributes',None)
        users.append(user)
    return users


@app.post("/setUserPassword/")
async def set_password(payload:User,Authorization: Annotated[str | None, Header()] = None):
    claims = auth(Authorization)

    user_group = claims['cognito:groups'][0]
    
    response = client.list_users_in_group(UserPoolId=USER_POOL_ID, GroupName=user_group)
    users = [user['Username'] for user in response['Users']]
    if (payload.username in users) or (user_group == 'admin'):
        try:
            response = client.admin_set_user_password(
                UserPoolId=USER_POOL_ID,
                Username=payload.username,
                Password=payload.password,
                Permanent=False
            )
        except Exception as err :
            raise HTTPException(status_code=400,detail=str(err))
    else:
        raise HTTPException(status_code=401,detail='not allowed')

    return response

@app.post("/createUser/{group}/")
async def create_user(group:str, payload:User, Authorization: Annotated[str | None, Header()] = None):
    print(payload)
    print(group)
    claims = auth(Authorization)
    user_group = claims['cognito:groups'][0]
    if (user_group != group) and (user_group != 'admin'):
        raise HTTPException(status_code=401,detail='not allowed')
    
    try:
        response = client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=payload.username,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': payload.email
                },
                {
                    'Name': 'given_name',
                    'Value': payload.given_name
                },
                {
                    'Name': 'family_name',
                    'Value': payload.family_name
                },
            ],

            TemporaryPassword=payload.password,
        )
        try:
            ## add user to group
            response = client.admin_add_user_to_group(
                UserPoolId=USER_POOL_ID,
                Username=payload.username,
                GroupName=group
            )
        except Exception as err :
            raise HTTPException(status_code=400,detail=str(err))
            
    except Exception as err :
        raise HTTPException(status_code=400,detail=str(err))
    return response


@app.post("/deleteUser/")
async def delete_user(payload:Username, Authorization: Annotated[str | None, Header()] = None):
    claims = auth(Authorization)

    user_group = claims['cognito:groups'][0]
    
    response = client.list_users_in_group(UserPoolId=USER_POOL_ID, GroupName=user_group)
    users = [user['Username'] for user in response['Users']]
    if (payload.username in users) or (user_group == 'admin'):
        try:
           response = client.admin_delete_user(
                        UserPoolId=USER_POOL_ID,
                        Username=payload.username
            )
        except Exception as err :
            raise HTTPException(status_code=400,detail=str(err))
    else:
        raise HTTPException(status_code=401,detail='not allowed')

    return response

handler = Mangum(app=app)