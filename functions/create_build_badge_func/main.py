import base64
import os
import json
from google.cloud import storage

def create_build_badge_func(data, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         data (dict): The dictionary with data specific to this type of event.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata.
    """

    if 'data' in data:
        buildstatusmessage = json.loads(base64.b64decode(data['data']).decode('utf-8'))
        print(buildstatusmessage)

        if 'status' in buildstatusmessage:
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(os.environ['STORAGE_BUCKET'])
            if buildstatusmessage['status'] == 'QUEUED' or buildstatusmessage['status'] == 'WORKING':
                status = 'pending'
            if buildstatusmessage['status'] == 'FAILURE':
                status = 'failing'
            if buildstatusmessage['status'] == 'SUCCESS':
                status = 'passing'
            bucket.copy_blob('badge-{}.png'.format(status), 'buildstatus.png')
