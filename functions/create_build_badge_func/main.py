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
        strdecoded = base64.b64decode(data['data']).decode('utf-8')
        buildstatusmessage = json.loads(strdecoded)
        print(buildstatusmessage)

        if 'status' in buildstatusmessage and 'source' in buildstatusmessage and 'repoSource' in buildstatusmessage['source']:
            if buildstatusmessage['status'] == 'QUEUED' or buildstatusmessage['status'] == 'WORKING':
                status = 'pending'
            if buildstatusmessage['status'] == 'FAILURE':
                status = 'failing'
            if buildstatusmessage['status'] == 'SUCCESS':
                status = 'passing'
            sourcefn = 'badge-{}.png'.format(status)
            destfn = 'status/{}-{}-status.png'.format(
                buildstatusmessage['source']['repoSource'].get('repoName',''),
                buildstatusmessage['source']['repoSource'].get('branchName',''))
            print('Copy from {} to {}'.format(sourcefn, destfn))
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(os.environ['STORAGE_BUCKET'])
            bucket.copy_blob(bucket.blob(sourcefn), bucket, destfn)
