import json
import sys
import os
import base64

from google.cloud import kms_v1
from google.oauth2 import service_account
import googleapiclient.discovery


if len(sys.argv) >= 1:
    projectsfile = open(sys.argv[1])
    projects = json.load(projectsfile)

    # Decrypt client_credentials to file
    adminsdk_credentials_encrypted = base64.b64decode(os.environ['ADMINSDK_CREDENTIALS_ENCRYPTED'])
    kms_client = kms_v1.KeyManagementServiceClient()
    crypto_key_name = kms_client.crypto_key_path_path(os.environ['PROJECT_ID'], 'europe-west1', 'admin-sdk', 'admin-sdk-credentials')
    decrypt_response = kms_client.decrypt(crypto_key_name, adminsdk_credentials_encrypted)
    with open('adminsdk_credentials.json', 'w') as outfile:
        json.dump(decrypt_response.plaintext, outfile)


    # Set ADMIN SDK credentials
    delegated_credentials = service_account.Credentials.from_service_account_file(
        'adminsdk_credentials.json',
        scopes=[os.environ['SERVICE_ACCOUNT_SCOPE']],
        subject=os.environ['USER_IMPERSONATION_EMAIL'])

    service = googleapiclient.discovery.build(
        'admin', 'directory_v1', credentials=delegated_credentials)

    print('Service has been created')


    # Set group
    group_object = service.groups().list(
        domain='vwt.digital',
        maxResults=1,
        query='email:{}*'.format(os.environ['GSUITE_GROUP_KEY']).split('@')[0])
    ).execute()

    # Create new group if not existing
    if 'groups' not in group_object:
        group_json = {
            "description": "All GCP cloud builder accounts",
            "name": "Cloud Builders",
            "email": '{}'.format(os.environ['GSUITE_GROUP_KEY']))
        }
        service.groups().insert(body=group_json).execute()

    print(F'Group "{os.environ['GSUITE_GROUP_KEY'])}" is active')


    # Getting all members of the group
    members_object = service.members().list(
        groupKey=os.environ['GSUITE_GROUP_KEY']),
        roles='MEMBER'
    ).execute()
    group_members = members_object.get('members')

    # Deleting all existing group members
    if group_members:
        for member in group_members:
            service.members().delete(
                groupKey=os.environ['GSUITE_GROUP_KEY']),
                memberKey=member['id']
            ).execute()

        print('All current group members are removed')

    # Add members to group
    for project in projects:
        new_user = {
            "status": "ACTIVE",
            "delivery_settings": "NONE",
            "role": "MEMBER",
            "type": "USER",
            "email": '{}@appspot.gserviceaccount.com'.format(project['projectId'])
        }
        service.members().insert(groupKey=os.environ['GSUITE_GROUP_KEY']), body=new_user).execute()

    print('All new group members are added')
