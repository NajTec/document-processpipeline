import json
import boto3

def lambda_handler(event, context):
    if 'JobStatus' in event:
        jobid = event['JobStatus']['JobId']
    else:
        jobid = event['JobId']

    key = event['Name']
    bucket = event['Bucket']
    uuid = event['id']
    
    textract_client = boto3.client("textract",region_name="eu-central-1")
    
    response = textract_client.get_document_text_detection(
        JobId = jobid
    )
    jobstatus = response['JobStatus']
    
    return {
        'Name': key,
        'id' : uuid,
        'Bucket' : bucket,
        'JobId': jobid,
        'DocumentDetection': {
            'jobStatus' : jobstatus
        }
    }
