import os
from io import BytesIO, StringIO
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import boto3


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.nan):
            return None
        return super(NpEncoder, self).default(obj)


class DataBase:
    def __init__(self,bucket_name):
        print('init db')
        self.BUCKET = bucket_name
        self.s3_resource = boto3.resource('s3')
        self.s3 = boto3.client('s3')    

    def read_geojson(self, uuid, name):
        path =  uuid  + '/' + name
        result = self.s3.get_object(Bucket=self.BUCKET, Key=path) 
        dict = json.load(result["Body"])
        return gpd.read_file(json.dumps(dict))
    
    def read_geojson_from_key(self, key):
        result = self.s3.get_object(Bucket=self.BUCKET, Key=key) 
        dict = json.load(result["Body"])
        return gpd.read_file(json.dumps(dict))
    
    def write_geojson(self, gdf, uuid, name):
        # Convert the GeoDataFrame to a GeoJSON string
        if 'index' not in gdf.columns:
            gdf = gdf.reset_index()
        geojson = gdf.to_json(drop_id=True)
        # Construct the S3 key (path)
        s3_key = f"{uuid}/{name}"
        # Write the GeoJSON data to the S3 bucket
        self.s3.put_object(Bucket=self.BUCKET, Key=s3_key, Body=geojson)
        
    
    def read_csv(self, uuid, name):
        path = os.path.join(uuid, name)
        obj = self.s3.get_object(Bucket=self.BUCKET, Key=path)
        return pd.read_csv(BytesIO(obj['Body'].read()))
    
    def save_csv(self, uuid, name, payload):
        '''
            parameters
            ----------
            payload: pandas df to send to s3 as csv.
            name: name of the file (with .csv at the end)
            returns
            ----------
        '''
        csv_buffer = StringIO()
        payload.to_csv(csv_buffer)

        filename =  uuid + '/' + name
        self.s3_resource.Object(self.BUCKET, filename).put(Body=csv_buffer.getvalue())

    def save_image(self, uuid, name, img_buffer):
        '''
            parameters
            ----------
            payload: pandas df to send to s3 as csv.
            name: name of the file (with .csv at the end)
            returns
            ----------
        '''
        img_buffer.seek(0)
        bucket = self.s3_resource.Bucket(self.BUCKET)
        filename =  uuid + '/' + name
        bucket.put_object(Body=img_buffer, ContentType='image/png', Key=filename)

