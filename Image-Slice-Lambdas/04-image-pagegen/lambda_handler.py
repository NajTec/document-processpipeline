import json
import boto3
import os
import io
import botocore
import time
#import numpy as np

#import cv2
from pdf2image import convert_from_path

s3_client = boto3.client('s3',
                        region_name='us-west-2')


def get_s3_object(s3_client,key,bucket,filename):
    new_file_key = os.path.abspath(os.path.join(os.sep, 'tmp', filename))
    try:
        response = s3_client.download_file(bucket,key,new_file_key)
        print("here")
    except botocore.exceptions.ClientError as e:
        print(e)
    return new_file_key

def upload_s3_object(s3_client,bucket,key,filename):
    try:
        s3_client.upload_file(filename,bucket,key)
    except botocore.exceptions.ClientError as e:
        print(e)

def upload_s3_byte(s3_client,bucket,key,byte):
    try:
        s3_client.put_object(Body=byte,Bucket=bucket,Key=key)
    except botocore.exceptions.ClientError as e:
        print(e)


def convert_pdf(filename,prefix,bucket):
    counter = 1
    pages = convert_from_path(filename, 500)
    for page in pages:
        key = "{}/pages/{}.png".format(prefix,counter)
        page_filename = '{}.png'.format(counter)
        new_file_key = os.path.abspath(os.path.join(os.sep, 'tmp', page_filename))
        page.save(new_file_key, 'PNG')
        counter = counter + 1
        upload_s3_object(s3_client=s3_client,bucket=bucket,key=key,filename=new_file_key)


def slice_images(folder,handwritten_json):
    list_of_handwritten_content = handwritten_json['handwritten_locations']
    
    for elem in list_of_handwritten_content:
        #elem = list_of_handwritten_content[0]
        bbox = elem["Geometry"]["BoundingBox"]
        text = elem["Text"]
        page = str(elem["Page"])
        img_path = "pages/{}.png".format(page)
        img = cv2.imread(img_path)
        x_1 = int(bbox['Left'] * img.shape[1])
        y_1 = int(bbox['Top'] * img.shape[0])
        width = int(bbox['Width'] * img.shape[1]) 
        height = int(bbox['Height'] * img.shape[0])
        cropped_image = img[y_1:y_1+height, x_1:x_1+width]
        upload_sliced_images(cropped_image,text)

    return None

def upload_sliced_images(cv_image,name):
    ts = event["classfied_key"].split('/')[0]
    doc_name = event["classfied_key"].split('/')[1]
    doc_key = "{}/{}/to_infer/{}.png".format(ts,doc_name,name)

    is_success, buffer = cv2.imencode(".png",cv_image)
    io_buf = io.BytesIO(buffer)
    
    upload_s3_byte(s3_client=s3_client,key=doc_key,bucket=event["classified_bucket"],byte=io_buf)
    return 200

def lambda_handler(event, context):
    #print(event)
    json_filename = event["classfied_key"].split("/")[4]
    ts_doc = event["classfied_key"].split("/")[0] + "/" + event["classfied_key"].split("/")[1]
    print(ts_doc)
    filename = get_s3_object(s3_client=s3_client,key=event["key"],bucket=event["bucket"],filename="tmp.pdf")
    convert_pdf(filename,ts_doc,event["classified_bucket"])

    return event



