from flask import Flask,jsonify,request
from flask_cors import CORS
import boto3
import autogluon.core as ag
from autogluon.vision import ImagePredictor
import os

app = Flask(__name__)
CORS(app)

filename = 'image_predictor.ag'
predictor_loaded = ImagePredictor.load(filename)
aws_access_key_id= os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key= os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name='eu-central-1')

def get_s3_object(s3_client,key,bucket,filename):
    print(aws_access_key_id)
    print(aws_secret_access_key)
    new_file_key = os.path.abspath(os.path.join(os.sep, 'tmp', filename))
    try:
        s3_client.download_file(bucket,key,new_file_key)
    except botocore.exceptions.ClientError as e:
        print(e)
    return new_file_key

#pred = predictor_loaded.predict(image)

@app.route("/",methods = ["GET"])
def index():
	return {"status":200}

@app.route("/inference", methods = ["POST"])
def make_inf():
	ret_json = {}
	if request.method == "POST":
		data = request.json
		list_of_signatures = []
		list_of_comments = []
		img_list = data["sliced_image_list"]
		classified_bucket = data["classified_bucket"]
		for elem in img_list:
			filename = elem.split("/")[4]
			doc_name = get_s3_object(s3_client=s3_client,key=elem,bucket=classified_bucket,filename=filename)
			print(doc_name)
			pred = predictor_loaded.predict(doc_name)
			if pred.iloc[0] == 1:
				list_of_signatures.append(doc_name.split("/")[2])
			else:
				list_of_comments.append(doc_name.split("/")[2])
		
		ret_json["signatures"] = list_of_signatures
		ret_json["comments"] = list_of_comments
		ret_json["status"] = 200
		ret_json["content"] = "application/json"
		return ret_json
	else:
		ret_json["status"] = 500
		return ret_json

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

