FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/mxnet-inference:1.8.0-cpu-py37-ubuntu16.04
COPY ./* ./app/
WORKDIR /app/
RUN pip3 install -r requirements.txt
EXPOSE 8080
CMD ["python3", "app.py"]
