from typing import Union
import requests
import os 
import pymongo
import io
import random

from fastapi import FastAPI, Request
from minio import Minio
from kubernetes import client, config

app = FastAPI()


@app.get("/")
def read_root(res: Request):

    some_bs_variable = ''
    
    res.headers
    # "SERVICE2_SERVICE_PORT"

    res = requests.get(f'http://{os.environ.get("SERVICE2_SERVICE_HOST")}/')
    

    return {
        'headers' : str(res.headers),
        'response' : res.__repr__()
    }


@app.get("/mongodb")
def read_mongo():
    mdbclient = pymongo.MongoClient(os.getenv('MONGODB_SERVICE_HOST'), int(os.getenv('MONGODB_SERVICE_PORT')),minPoolSize=0, maxPoolSize=200)

    db = mdbclient["taskdb"]
    db_col = db["tasks"]


    result = db_col.insert_one({'hello' : 'my guy'})

    return str(result)


def generate_random_binary_data(size=1024):
    return bytes([random.randint(0, 255) for _ in range(size)])

def create_random_binary_file(size=1024):
    content = generate_random_binary_data(size)
    buffer = io.BytesIO(content)
    return buffer

@app.get("/minio")
def read_minio(req: Request):
    # {os.environ.get("MINIO_SERVICE_HOST")}


    client = Minio(f'{os.environ.get("MINIO_DNS_NAME")}:{os.environ.get("MINIO_SERVICE_PORT")}',
          access_key=os.environ.get('MINIO_ROOT_USERNAME'),
          secret_key=os.environ.get('MINIO_ROOT_PASSWORD'),
          secure=False)
    
    # Example: Create a random binary file with a size of 1024 bytes
    random_binary_buffer = create_random_binary_file(1024)

    b_upload = io.BytesIO(random_binary_buffer.getvalue())

    try: 
        client.make_bucket('temp-bucket')
    except:
        ...

    client.put_object(
                bucket_name='temp-bucket', #perhaps use an environment variable?
                object_name='testfile.txt', #filename + sudopath 'x/core/filename.ome.tiff'
                data=b_upload, #ENV Variable for setting the number of parallel uploads MINIO can use
                length=b_upload.getbuffer().nbytes
            )
    
    return str(client.get_presigned_url(
        'GET',
        bucket_name='temp-bucket',
        object_name='testfile.txt',)) + f" | {req.base_url}"

    

@app.get('/k8s/{image_name}')
def k8s_job(image_name: str):
    # Configs can be set in Configuration class directly or using helper utility
    config.load_incluster_config()
    # v1 = client.CoreV1Api()

    # Create a Namespace object
    namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name="your-namespace"))

    
    # Create the Namespace
    api_instance = client.CoreV1Api()
    try:
        api_instance.create_namespace(body=namespace)
    except:
        ...
    api_instance = client.BatchV1Api()
    # Create empty job
    job = client.V1Job()
    # define job metadata
    job.metadata = client.V1ObjectMeta(name=f"my-job-name-{1000}")
    
    # command = ["/bin/sh", "-c", "echo Hello, Kubernetes! $CINCODEBIO_DATA_PAYLOAD"]
    # Define the container
    container = client.V1Container(
        name="my-container",
        image=f"localhost:32000/{image_name}:registry",
        env=[
            client.V1EnvVar(
                name="CINCODEBIO_DATA_PAYLOAD",
                value='SOMEJSONSTRING'
            ),
        ]
    )

    # define the job-spec
    job.spec = client.V1JobSpec(
        ttl_seconds_after_finished=60, # this deletes the jobs from the namespace after completion.
        template=client.V1PodTemplateSpec(
            spec=client.V1PodSpec(containers=[container],restart_policy="Never")
        ),
        # pod_failure_policy=client.V1PodFailurePolicy(
        #     rules=[client.V1PodFailurePolicyRule(action='FailIndex')]
        # ),
        
    )

    

    return str(api_instance.create_namespaced_job(namespace="your-namespace", body=job))