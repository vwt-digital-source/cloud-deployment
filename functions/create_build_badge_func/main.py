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
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(os.environ['STORAGE_BUCKET'])
        bucket.copy_blob('

