import base64
import os
import json
import requests
from google.cloud import kms_v1


def parse_status(payload):
    status = 'pending'
    if payload['status'] == 'QUEUED' or payload['status'] == 'WORKING':
        status = 'pending'
    if payload['status'] in ['FAILURE', 'TIMEOUT', 'CANCELLED']:
        status = 'failing'
    if payload['status'] == 'SUCCESS':
        status = 'passing'

    return status


class DBProcessor(object):
    def __init__(self):
        pass

    def process(self, payload):
        if 'status' in payload and \
                'source' in payload and \
                'repoSource' in payload['source'] and \
                'sourceProvenance' in payload and \
                'resolvedRepoSource' in payload['sourceProvenance']:

            status = parse_status(payload)

            github_status = {
                'state': status,
                'description': 'GCP Cloud Build reported: {}'.format(
                    payload['status']),
                'context': 'gcp/cloudbuild'
            }
            if 'logUrl' in payload:
                github_status['target_url'] = payload['logUrl']

            repo_id_parts = \
                payload['sourceProvenance']['resolvedRepoSource'][
                    'repoName'].split('_')
            if repo_id_parts[0] == 'github' and len(repo_id_parts) == 3:
                user = repo_id_parts[1]
                repo_name = repo_id_parts[2]
                commit_sha = \
                    payload['sourceProvenance']['resolvedRepoSource'][
                        'commitSha']

                github_access_token_encrypted = base64.b64decode(
                    os.environ['GITHUB_ACCESS_TOKEN_ENCRYPTED'])
                kms_client = kms_v1.KeyManagementServiceClient()
                crypto_key_name = kms_client.crypto_key_path_path(
                    os.environ['PROJECT_ID'], 'europe-west1',
                    'github', 'github-access-token')
                decrypt_response = kms_client.decrypt(
                    crypto_key_name, github_access_token_encrypted)
                github_access_token = decrypt_response.plaintext \
                    .decode("utf-8").replace('\n', '')

                github_url = \
                    'https://api.github.com/repos/{}/{}/statuses/{}'.format(
                        user, repo_name, commit_sha)
                headers = {'Content-Type': 'application/json',
                           'Authorization': 'Bearer '+github_access_token}
                print('POST to {}: {}'.format(github_url,
                                              json.dumps(github_status)))
                post_result = requests.post(github_url, headers=headers,
                                            data=json.dumps(github_status))
                print('POST result code {}, data {}'.format(
                    post_result.status_code, post_result.text))
                post_result.raise_for_status()
