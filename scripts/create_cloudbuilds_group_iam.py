#!/usr/bin/env python3

import json
import sys
import os
import base64

from google.cloud import kms_v1
from google.oauth2 import service_account
import googleapiclient.discovery

print('File initiated')

if len(sys.argv) >= 1:
    projectsfile = open(sys.argv[1])
    projects = json.load(projectsfile)

    # Decrypt client_credentials to file
    adminsdk_credentials_encrypted = base64.b64decode(os.environ['ADMINSDK_CREDENTIALS_ENCRYPTED'])
    kms_client = kms_v1.KeyManagementServiceClient()
    crypto_key_name = kms_client.crypto_key_path_path(os.environ['PROJECT_ID'], 'europe-west1', 'admin-sdk', 'admin-sdk-credentials')
    decrypt_response = kms_client.decrypt(crypto_key_name, adminsdk_credentials_encrypted)
    with open('adminsdk_credentials.json', 'w') as outfile:
        outfile.write(decrypt_response.plaintext.decode("utf-8").replace('\n', ''))


    # Set ADMIN SDK credentials
    delegated_credentials = service_account.Credentials.from_service_account_file(
        'adminsdk_credentials.json',
        scopes=[sys.argv[3]],
        subject=sys.argv[2])

    service = googleapiclient.discovery.build(
        'admin', 'directory_v1', credentials=delegated_credentials)

    print('Service has been created')


    # Set group
    group_object = service.groups().list(
        domain='vwt.digital',
        maxResults=1,
        query='email:{}*'.format(sys.argv[4].split('@')[0])
    ).execute()

    # Create new group if not existing
    if 'groups' not in group_object:
        group_json = {
            "description": "All GCP {} cloud builder accounts".format(os.environ['BRANCH_NAME']),
            "name": "Cloud Builders {}".format(os.environ['BRANCH_NAME']),
            "email": '{}'.format(sys.argv[4])
        }
        service.groups().insert(body=group_json).execute()

    print('Group "{}" is active'.format(sys.argv[4]))

    # Create list with all project emails
    project_ids = []
    for project in projects['projects']:
        project_ids.append('{}@appspot.gserviceaccount.com'.format(project['projectId']))

    # Getting all members of the group
    members_object = service.members().list(
        groupKey=sys.argv[4],
        roles='MEMBER'
    ).execute()
    group_members = members_object.get('members')

    if group_members:
        # Create list with existing group emails
        group_member_ids = []
        for member in group_members:
            group_member_ids.append(member['email'])

        # Compare existing with new emails
        to_remove = list(set(group_member_ids).difference(project_ids))
        project_ids = list(set(project_ids).difference(group_member_ids))

        if len(to_remove) > 0:
            # Remove all emails from group that are not in projects list
            for project_id in to_remove:
                service.members().delete(
                    groupKey=sys.argv[4],
                    memberKey=project_id
                ).execute()

        print('{} non-existing projects have been deleted from the group'.format(len(to_remove)))

    # Add new projects to group
    for project_id in project_ids:
        new_user = {
            "status": "ACTIVE",
            "delivery_settings": "NONE",
            "role": "MEMBER",
            "type": "USER",
            "email": '{}'.format(project_id)
        }
        service.members().insert(groupKey=sys.argv[4], body=new_user).execute()

    print('{} projects have been added to the group'.format(len(project_ids)))
