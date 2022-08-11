import json
import cv2
import boto3
import os
import io
import botocore
import time

s3_client = boto3.client('s3',
                        region_name='eu-central-1')
                        
def get_s3_object(s3_client,key,bucket,filename):
    new_file_key = os.path.abspath(os.path.join(os.sep, 'tmp', filename))
    print(new_file_key)
    response = s3_client.download_file(bucket,key,new_file_key)
    print(response)
    return new_file_key

def slice_images(folder,handwritten_json,bucket):
    list_of_handwritten_content = handwritten_json['handwritten_locations']
    list_of_sliced_image_keys = []
    
    for elem in list_of_handwritten_content:
        #elem = list_of_handwritten_content[0]
        bbox = elem["Geometry"]["BoundingBox"]
        content_id = elem["Id"]
        page = str(elem["Page"])
        key = "{}{}.png".format(folder,page)
        filename = "{}.png".format(page)
        img_path = get_s3_object(s3_client,key,bucket,filename)
        img = cv2.imread(img_path)
        x_1 = int(bbox['Left'] * img.shape[1])
        y_1 = int(bbox['Top'] * img.shape[0])
        width = int(bbox['Width'] * img.shape[1]) 
        height = int(bbox['Height'] * img.shape[0])
        cropped_image = img[y_1:y_1+height, x_1:x_1+width]
        img_key = upload_sliced_images(cropped_image,content_id,key,bucket)
        list_of_sliced_image_keys.append(img_key)

    return list_of_sliced_image_keys
#    
def upload_sliced_images(cv_image,name,key,bucket): #id hinzufügen
    ts = key.split('/')[0]
    doc_name = key.split('/')[1]
    doc_key = "{}/{}/to_infer/{}.png".format(ts,doc_name,name)

    is_success, buffer = cv2.imencode(".png",cv_image)
    io_buf = io.BytesIO(buffer)
    
    upload_s3_byte(s3_client=s3_client,key=doc_key,bucket=bucket,byte=io_buf)
    return doc_key
    
def upload_s3_byte(s3_client,bucket,key,byte):
    try:
        s3_client.put_object(Body=byte,Bucket=bucket,Key=key)
    except botocore.exceptions.ClientError as e:
        print(e)

def lambda_handler(event, context):
    json_filename = event["classfied_key"].split("/")[4]
    print(json_filename)
    page_prefix = "{}/{}/pages/".format(event["classfied_key"].split("/")[0],event["classfied_key"].split("/")[1])
    json_name = get_s3_object(s3_client=s3_client,key=event["classfied_key"],bucket=event["classified_bucket"],filename=json_filename)
    with open(json_name) as json_file:
        handwritten_dict = json.load(json_file)
    event["sliced_image_keys"] = slice_images(page_prefix,handwritten_dict,event["classified_bucket"])
    

    return event
