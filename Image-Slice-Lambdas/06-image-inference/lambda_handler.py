import json
import boto3
import requests
import os
import botocore

s3_client = boto3.client('s3',
                        region_name='us-west-2')
                        
url = "http://internal-NewMLInference-1836312875.eu-central-1.elb.amazonaws.com/inference"

# get s3 object 
def get_s3_object(s3_client,key,bucket,filename):
    new_file_key = os.path.abspath(os.path.join(os.sep, 'tmp', filename))
    try:
        response = s3_client.download_file(bucket,key,new_file_key)
        print("here")
    except botocore.exceptions.ClientError as e:
        print(e)
    return new_file_key

# infer ml model
def inference_model(s3_client,image_list,bucket):
    myobj = {"sliced_image_list": image_list,"classified_bucket":bucket}
    print(image_list)
    response = requests.post(url, json = myobj)
    return response

def generate_message(content_list,handwritten_json,content_type,doc_name):
    handwritten_content = handwritten_json["handwritten_locations"]
    id_list = get_id_list(content_list)
    messages = []
    
    for idx in id_list:
        for elem in handwritten_content:
            if elem["Id"] == idx:
                messages.append("Following {} {} detected on {} in this document on Page {}".format(content_type,elem["Text"],doc_name,elem["Page"]))
    
    return messages

def get_id_list(content_list):
    ids = []
    for elem in content_list:
        elem = elem.replace("/tmp/","") #richtige version auskommentiert
        content_id = elem.split(".")[0]
        ids.append(content_id)
    return ids

def get_docname(key):
    return None
#
def lambda_handler(event, context):
    json_filename=event["classfied_key"].split("/")[2]
    key = event["key"]
    sliced_images = event["sliced_image_keys"]
    classified_bucket = event["classified_bucket"]
    response = inference_model(s3_client,sliced_images,classified_bucket)
    print(response.text)
    response_dict = json.loads(response.text)
    signatures = response_dict["signatures"]
    comments = response_dict["comments"]
    
    json_name = get_s3_object(s3_client=s3_client,key=event["classfied_key"],bucket=event["classified_bucket"],filename=json_filename)
    with open(json_name) as json_file:
        handwritten_dict = json.load(json_file)
    
    list_of_messages_signature = generate_message(signatures,handwritten_dict,"signature",key)
    list_of_messages_comments = generate_message(comments,handwritten_dict,"comments",key)
    
    return {
        'signatures': list_of_messages_signature,
        'comments' : list_of_messages_comments
    }
