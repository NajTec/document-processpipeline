import json
import boto3
import botocore
from datetime import datetime
import time

                
input_bucket = "inputbucket"
processed_bucket = "processed-bucket"
classified_bucket = "classified-bucket"
textract_client = boto3.client('textract',
                                    region_name='eu-central-1')
s3_client = boto3.client('s3',
                        region_name='eu-central-1')

def iterate_bucket_items(bucket,s3_client):
    client = s3_client
    try:
        paginator = client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket)
    except botocore.exceptions.ClientError as e:
        logging.error(e)
        return None

    for page in page_iterator:
        if page['KeyCount'] > 0:
            for item in page['Contents']:
                yield item

def get_textract_results(textract_client,job_id,text_type):
    
    list_of_handwritten_content = []
    
    response = textract_client.get_document_text_detection(
            JobId = job_id
        )
    
    for elem in response['Blocks']:
                if elem['BlockType'] == 'WORD':
                    if elem['TextType'] == 'HANDWRITING':
                        list_of_handwritten_content.append(elem)
    # Job failed or Error
    if response['JobStatus'] == 'FAILED':
        return {
            'statusCode' : 404
        }
    elif response['JobStatus'] == 'ERROR':
        return {
            'statusCode' : 500
        }
    else:
        while response.get('NextToken') != None:
            for elem in response['Blocks']:
                if elem['BlockType'] == 'WORD':
                    if elem['TextType'] == 'HANDWRITING':
                        print("handwriting detected")
                        list_of_handwritten_content.append(elem)
                                
            response = textract_client.get_document_text_detection(
                JobId = job_id,
                NextToken = response['NextToken']
                )
            #print(list_of_handwritten_content)
                
    return list_of_handwritten_content
    
def write_s3_bucket(s3_client,content_type,key,bucket,payload):
    json_to_classified = {}
    json_to_classified['handwritten_locations'] = payload
    
    result = s3_client.put_object(Body=json.dumps(json_to_classified),Bucket=bucket,Key=key)
        
    return result
    
def move_s3_bucket(s3_client,key_source,key_target,bucket_source,bucket_target):
    copy_source = {
        'Bucket': bucket_source,
        'Key': key_source
    }
    result = s3_client.copy(copy_source, processed_bucket, key_target)
    return result
    
#def delete_s3_bucket(s3_client,key,bucket):
#    try:
#        result = s3_client.delete_object(
#                Bucket=bucket,
#                Key=key
#            )
#    except botocore.exceptions.ClientError as e:
#        print(e)
#    return result
    
def lambda_handler(event, context):
    job_id = event['JobId']
    key = event['Name']
    bucket = event['Bucket']
    uuid = event['id']
    now = datetime.now()
    ts_string = now.strftime("%m.%d.%Y-%H:%M:%S/")
    json_name = key.split('.')
    filename = json_name[0]
    json_name = json_name[0] + '.json'
    
   
    text_type = 'HANDWRITING'
    new_key = '{}/{}{}/handwritten/{}'.format(uuid,ts_string,key,json_name)
    #new_key = '{}{}/handwritten/{}'.format(ts_string,key,json_name)
    print(new_key)
    processed_key = ts_string + key + '/' + json_name
    
    result = get_textract_results(textract_client=textract_client,job_id=job_id,text_type=text_type)
    
    returnval = write_s3_bucket(s3_client=s3_client,content_type=text_type,key=new_key,bucket=classified_bucket,payload=result)
    
    move_s3_bucket(s3_client=s3_client,key_source=key,bucket_source=bucket,key_target=processed_key,bucket_target=processed_bucket)
    
    return {
        'statusCode': 200,
        'classfied_key': new_key,
        'classified_bucket': classified_bucket,
        'key':key,
        'bucket':bucket
    }
