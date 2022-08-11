import uuid

def lambda_handler(event, context):
	uuid = uuid.generate()
	event["id"] = uuid
return {event}