import base64
import os
import json
import requests
from google.cloud import kms_v1

def report_build_status_github_func(data, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         data (dict): The dictionary with data specific to this type of event.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata.
    """

    if 'data' in data:
        strdecoded = base64.b64decode(data['data']).decode('utf-8')
        buildstatusmessage = json.loads(strdecoded)
        print('RECEIVED {}'.format(json.dumps(buildstatusmessage)))

        if 'status' in buildstatusmessage and 'source' in buildstatusmessage and 'repoSource' in buildstatusmessage['source'] \
                and 'sourceProvenance' in buildstatusmessage and 'resolvedRepoSource' in buildstatusmessage['sourceProvenance']:

            status = 'pending'
            if buildstatusmessage['status'] == 'QUEUED' or buildstatusmessage['status'] == 'WORKING':
                status = 'pending'
            if buildstatusmessage['status'] in ['FAILURE', 'TIMEOUT']:
                status = 'failure'
            if buildstatusmessage['status'] == 'SUCCESS':
                status = 'success'

            github_status = {
                'state': status,
                'description': 'GCP Cloud Build reported: {}'.format(buildstatusmessage['status']),
                'context': 'gcp/cloudbuild'
            }
            if 'logUrl' in buildstatusmessage:
                github_status['target_url'] = buildstatusmessage['logUrl']

            repo_id_parts = buildstatusmessage['sourceProvenance']['resolvedRepoSource']['repoName'].split('_')
            if repo_id_parts[0] == 'github' and len(repo_id_parts) == 3:
                user = repo_id_parts[1]
                repo_name = repo_id_parts[2]
                commitSha = buildstatusmessage['sourceProvenance']['resolvedRepoSource']['commitSha']

                github_access_token_encrypted = base64.b64decode(os.environ['GITHUB_ACCESS_TOKEN_ENCRYPTED'])
                kms_client = kms_v1.KeyManagementServiceClient()
                crypto_key_name = kms_client.crypto_key_path_path(os.environ['PROJECT_ID'], 'europe-west1', 'github', 'github-access-token')
                decrypt_response = kms_client.decrypt(crypto_key_name, github_access_token_encrypted)
                github_access_token = decrypt_response.plaintext.decode("utf-8").replace('\n', '')

                github_url = 'https://api.github.com/repos/{}/{}/statuses/{}'.format(user, repo_name, commitSha)
                headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+github_access_token}
                print('POST to {}: {}'.format(github_url, json.dumps(github_status)))
                post_result = requests.post(github_url, headers=headers, data=json.dumps(github_status))
                print('POST result code {}, data {}'.format(post_result.status_code, post_result.text))
                post_result.raise_for_status()
